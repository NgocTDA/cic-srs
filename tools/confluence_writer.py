#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import re
import hashlib
import argparse
import urllib3
import requests
import markdown
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from PIL import Image

# Kích thước hiển thị tối đa khi chèn ảnh vào Confluence (ac:width, px) — chỉ
# là trần, không phóng to ảnh nhỏ hơn. Ảnh đứng độc lập rộng hơn bảng vì
# không bị ràng buộc bởi cột.
STANDALONE_IMAGE_MAX_WIDTH = 1200
TABLE_IMAGE_MAX_WIDTH = 600

# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def load_env(env_path=None):
    env_vars = {}
    search_paths = []
    if env_path:
        search_paths.append(env_path)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        search_paths.extend([
            os.path.join(os.getcwd(), '.env'),
            os.path.join(script_dir, '.env'),
            os.path.join(os.path.dirname(script_dir), '.env'),
        ])
    for path in search_paths:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        k, v = line.split('=', 1)
                        env_vars[k.strip()] = v.strip()
            return env_vars
    return env_vars


def _env_int(env, key, default):
    try:
        return int(env.get(key, default))
    except (TypeError, ValueError):
        return default


def _env_float(env, key, default):
    try:
        return float(env.get(key, default))
    except (TypeError, ValueError):
        return default


class ConfluenceClient:
    def __init__(self, base_url, token=None, auth_mode='bearer', username=None,
                 password=None, verify_ssl=True, connect_timeout=5, read_timeout=30,
                 max_retries=3, backoff_factor=1):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.auth_mode = auth_mode
        self.basic_auth = (username, password) if auth_mode == 'basic' else None
        self.verify = verify_ssl
        self.timeout = (connect_timeout, read_timeout)

        if auth_mode == 'basic':
            self.headers = {'Content-Type': 'application/json'}
        else:
            self.headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }

        # requests không tự retry — mount Retry qua HTTPAdapter. Chỉ các
        # method mặc định của urllib3 (GET/PUT/DELETE/HEAD/OPTIONS) được
        # retry tự động; POST (tạo trang, upload ảnh) không retry để tránh
        # tạo trùng khi request trước đã thành công nhưng response bị mất.
        retry = Retry(total=max_retries, backoff_factor=backoff_factor,
                      status_forcelist=(429, 500, 502, 503, 504))
        adapter = HTTPAdapter(max_retries=retry)
        self.session = requests.Session()
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def _kwargs(self, headers=None):
        kw = {'headers': headers or self.headers, 'verify': self.verify, 'timeout': self.timeout}
        if self.basic_auth:
            kw['auth'] = self.basic_auth
        return kw

    def _get(self, endpoint):
        res = self.session.get(self.base_url + endpoint, **self._kwargs())
        res.raise_for_status()
        return res.json()

    def _post(self, endpoint, data=None):
        res = self.session.post(self.base_url + endpoint, json=data, **self._kwargs())
        res.raise_for_status()
        return res.json()

    def _put(self, endpoint, data=None):
        res = self.session.put(self.base_url + endpoint, json=data, **self._kwargs())
        res.raise_for_status()
        return res.json()

    def get_page(self, page_id):
        return self._get(f"/rest/api/content/{page_id}?expand=version,body.storage")

    def create_page(self, space_key, title, parent_id=None, content=""):
        data = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": {
                "storage": {
                    "value": content,
                    "representation": "storage"
                }
            }
        }
        if parent_id:
            data["ancestors"] = [{"id": str(parent_id)}]
        return self._post("/rest/api/content", data)

    def update_page(self, page_id, title, new_version, content=""):
        data = {
            "version": {"number": new_version},
            "title": title,
            "type": "page",
            "body": {
                "storage": {
                    "value": content,
                    "representation": "storage"
                }
            }
        }
        return self._put(f"/rest/api/content/{page_id}", data)

    def get_attachments(self, page_id):
        return self._get(f"/rest/api/content/{page_id}/child/attachment?limit=100")

    def upload_attachment(self, page_id, file_path, attachment_id=None):
        filename = os.path.basename(file_path)
        with open(file_path, 'rb') as f:
            files = {'file': (filename, f, 'application/octet-stream')}
            headers = {'X-Atlassian-Token': 'no-check'}
            if self.auth_mode != 'basic':
                headers['Authorization'] = f'Bearer {self.token}'

            if attachment_id: # Update existing
                url = f"{self.base_url}/rest/api/content/{page_id}/child/attachment/{attachment_id}/data"
            else: # Create new
                url = f"{self.base_url}/rest/api/content/{page_id}/child/attachment"

            res = self.session.post(url, files=files, **self._kwargs(headers=headers))
            res.raise_for_status()
            return res.json()

    def download_attachment_content(self, download_path):
        url = self.base_url + download_path
        headers = {} if self.auth_mode == 'basic' else {'Authorization': f'Bearer {self.token}'}
        res = self.session.get(url, **self._kwargs(headers=headers))
        res.raise_for_status()
        return res.content

def calculate_md5(content_bytes):
    return hashlib.md5(content_bytes).hexdigest()

def calculate_file_md5(file_path):
    with open(file_path, 'rb') as f:
        return calculate_md5(f.read())

def _get_image_width(path):
    """Chiều rộng gốc (px) của file ảnh, None nếu không đọc được."""
    try:
        with Image.open(path) as im:
            return im.size[0]
    except Exception:
        return None


def _parse_css_width_px(value):
    """'120px' -> 120, '120' -> 120, '50%' hoặc rỗng -> None (không quy đổi
    được sang px tuyệt đối)."""
    if not value:
        return None
    value = value.strip()
    m = re.match(r'^(\d+(?:\.\d+)?)\s*px$', value, re.IGNORECASE)
    if m:
        return int(float(m.group(1)))
    if re.match(r'^\d+(?:\.\d+)?$', value):
        return int(float(value))
    return None


def _extract_width_attr(tag):
    """Đọc width khai trên chính tag (style="width:...px" hoặc width="...")."""
    if tag is None:
        return None
    style = tag.get('style', '')
    m = re.search(r'width\s*:\s*([^;]+)', style, re.IGNORECASE)
    if m:
        px = _parse_css_width_px(m.group(1))
        if px:
            return px
    return _parse_css_width_px(tag.get('width'))


def _find_column_width_px(img_tag):
    """Độ rộng cột (px) chứa ảnh, nếu bảng khai rõ — qua width/style trên
    chính ô <td>/<th>, hoặc <colgroup><col> cùng vị trí cột. Markdown thường
    (không chèn HTML thô) không khai width nào cả -> trả None, gọi nơi dùng
    tự rơi về mức trần mặc định. Không xử lý colspan (hiếm gặp, bỏ qua)."""
    cell = img_tag.find_parent(['td', 'th'])
    if cell is None:
        return None

    px = _extract_width_attr(cell)
    if px:
        return px

    table = cell.find_parent('table')
    row = cell.find_parent('tr')
    if table is None or row is None:
        return None

    cells = row.find_all(['td', 'th'], recursive=False)
    try:
        col_index = cells.index(cell)
    except ValueError:
        return None

    cols = table.find_all('col')
    if col_index < len(cols):
        return _extract_width_attr(cols[col_index])
    return None


def compute_display_width(local_path, in_table, column_width_px):
    """Kích thước ac:width cuối cùng: trần theo vị trí (bảng/độc lập), ưu
    tiên độ rộng cột nếu bảng khai rõ, không bao giờ phóng to ảnh gốc."""
    actual_width = _get_image_width(local_path)
    if actual_width is None:
        return None
    if in_table:
        cap = min(column_width_px, TABLE_IMAGE_MAX_WIDTH) if column_width_px else TABLE_IMAGE_MAX_WIDTH
    else:
        cap = STANDALONE_IMAGE_MAX_WIDTH
    return min(actual_width, cap)


def extract_image_paths(md_content):
    # Match markdown images: ![alt](path)
    md_img_pattern = r'!\[.*?\]\((.*?)\)'
    paths = re.findall(md_img_pattern, md_content)
    
    # Match Confluence macros: <ri:attachment ri:filename="path" />
    macro_img_pattern = r'<ri:attachment\s+ri:filename="([^"]+)"'
    paths.extend(re.findall(macro_img_pattern, md_content))
    return list(set(paths))

def main():
    parser = argparse.ArgumentParser(description="Upload Markdown file to Confluence Page.")
    parser.add_argument("--file", required=True, help="Path to the Markdown file")
    parser.add_argument("--title", help="Title of the page (defaults to filename)")
    parser.add_argument("--page-id", help="ID of an existing page to update")
    parser.add_argument("--parent-id", help="ID of parent page if creating a new page")
    parser.add_argument("--space", help="Confluence space key (defaults to CONFLUENCE_SPACE in .env)")
    parser.add_argument("--force-update-images", action="store_true", help="Force re-upload of all images even if hash matches")
    args = parser.parse_args()

    if not args.page_id and not args.parent_id:
        print("Error: Must provide either --page-id to update, or --parent-id to create a new page.")
        sys.exit(1)

    env = load_env()
    token = env.get("CONFLUENCE_TOKEN")
    base_url = env.get("CONFLUENCE_URL")
    space_key = args.space or env.get("CONFLUENCE_SPACE", "CIC")

    if not base_url:
        print("Error: Missing CONFLUENCE_URL in environment.")
        sys.exit(1)

    auth_mode = env.get("CONFLUENCE_AUTH_MODE", "bearer").strip().lower()
    username = env.get("CONFLUENCE_USERNAME")
    password = env.get("CONFLUENCE_PASSWORD")
    if auth_mode == "basic":
        if not (username and password):
            print("Error: CONFLUENCE_AUTH_MODE=basic requires CONFLUENCE_USERNAME "
                  "and CONFLUENCE_PASSWORD in .env.")
            sys.exit(1)
    elif auth_mode == "bearer":
        if not token:
            print("Error: Missing CONFLUENCE_TOKEN in environment.")
            sys.exit(1)
    else:
        print(f"Error: Unknown CONFLUENCE_AUTH_MODE '{auth_mode}' (expected 'bearer' or 'basic').")
        sys.exit(1)

    allow_insecure_http = env.get("CONFLUENCE_ALLOW_INSECURE_HTTP", "false").lower() == "true"
    if base_url.lower().startswith("http://") and not allow_insecure_http:
        print("Error: CONFLUENCE_URL dùng http:// nhưng CONFLUENCE_ALLOW_INSECURE_HTTP "
              "không phải 'true'. Dùng https:// hoặc khai CONFLUENCE_ALLOW_INSECURE_HTTP=true "
              "nếu đây là mạng nội bộ tin cậy.")
        sys.exit(1)

    verify_ssl = env.get("CONFLUENCE_VERIFY_TLS", "true").lower() == "true"
    client = ConfluenceClient(
        base_url, token=token, auth_mode=auth_mode, username=username, password=password,
        verify_ssl=verify_ssl,
        connect_timeout=_env_int(env, "CONFLUENCE_CONNECT_TIMEOUT", 5),
        read_timeout=_env_int(env, "CONFLUENCE_READ_TIMEOUT", 30),
        max_retries=_env_int(env, "CONFLUENCE_MAX_RETRIES", 3),
        backoff_factor=_env_float(env, "CONFLUENCE_BACKOFF_FACTOR", 1),
    )

    md_path = os.path.abspath(args.file)
    if not os.path.exists(md_path):
        print(f"Error: File {md_path} not found.")
        sys.exit(1)

    md_dir = os.path.dirname(md_path)
    title = args.title or os.path.splitext(os.path.basename(md_path))[0]
    
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Step 1: Create or fetch page
    if args.page_id:
        print(f"Fetching existing page {args.page_id}...")
        page_info = client.get_page(args.page_id)
        page_id = args.page_id
        version = page_info['version']['number']
        title = args.title if args.title else page_info['title']
    else:
        print(f"Creating placeholder page under parent {args.parent_id}...")
        page_info = client.create_page(space_key, title, parent_id=args.parent_id, content="<p>Uploading content...</p>")
        page_id = page_info['id']
        version = 1

    # Step 2: Handle Attachments
    image_paths = extract_image_paths(md_content)
    existing_attachments = {}
    if image_paths:
        print(f"Fetching existing attachments for page {page_id}...")
        try:
            att_data = client.get_attachments(page_id)
            for att in att_data.get('results', []):
                existing_attachments[att['title']] = att
        except Exception as e:
            print(f"Warning: Could not fetch attachments: {e}")

    for img_path in image_paths:
        if img_path.startswith('http://') or img_path.startswith('https://'):
            continue # Skip remote images
            
        local_path = os.path.join(md_dir, img_path)
        if not os.path.exists(local_path):
            print(f"Warning: Local image not found: {local_path}")
            continue

        filename = os.path.basename(local_path)
        att_exists = filename in existing_attachments
        
        if att_exists and not args.force_update_images:
            print(f"Checking hash for existing attachment: {filename}...")
            local_md5 = calculate_file_md5(local_path)
            
            att = existing_attachments[filename]
            download_url = att['_links']['download']
            try:
                remote_content = client.download_attachment_content(download_url)
                remote_md5 = calculate_md5(remote_content)
                if local_md5 == remote_md5:
                    print(f" -> Hash matches ({local_md5}), skipping upload.")
                    continue
                else:
                    print(f" -> Hash mismatch (Local: {local_md5}, Remote: {remote_md5}), updating...")
            except Exception as e:
                print(f" -> Error downloading remote attachment for hash check: {e}. Will upload.")
        elif att_exists:
            print(f"Force updating attachment: {filename}...")
        else:
            print(f"Uploading new attachment: {filename}...")

        att_id = existing_attachments[filename]['id'] if att_exists else None
        try:
            client.upload_attachment(page_id, local_path, attachment_id=att_id)
            print(f" -> Success!")
        except Exception as e:
            print(f" -> Failed to upload {filename}: {e}")

    # Step 3: Convert Markdown to HTML and inject macros
    print("Converting Markdown to Confluence Storage Format...")
    html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if src.startswith('http'):
            continue

        filename = os.path.basename(src)
        local_path = os.path.join(md_dir, src)

        ac_attrs = {}
        if os.path.exists(local_path):
            in_table = img.find_parent('table') is not None
            column_width_px = _find_column_width_px(img) if in_table else None
            width = compute_display_width(local_path, in_table, column_width_px)
            if width:
                ac_attrs['ac:width'] = str(width)
        else:
            print(f"Warning: Local image not found for sizing: {local_path}")

        ac_image = soup.new_tag('ac:image', **ac_attrs)
        ri_attachment = soup.new_tag('ri:attachment', **{'ri:filename': filename})
        ac_image.append(ri_attachment)
        img.replace_with(ac_image)

    final_html = str(soup)
    
    # Fix XML macros that might have been escaped by markdown
    final_html = re.sub(r'&lt;ac:image(.*?)&gt;', r'<ac:image\1>', final_html)
    final_html = re.sub(r'&lt;/ac:image&gt;', r'</ac:image>', final_html)
    final_html = re.sub(r'&lt;ri:attachment(.*?)&gt;', r'<ri:attachment\1>', final_html)
    final_html = re.sub(r'&lt;ri:attachment(.*?)/&gt;', r'<ri:attachment\1/>', final_html)

    # Step 4: Update page
    print(f"Updating page {page_id} with final content...")
    try:
        client.update_page(page_id, title, version + 1, final_html)
        print("Page updated successfully!")
        
        webui_link = f"{base_url.rstrip('/')}/spaces/{space_key}/pages/{page_id}"
        print(f"View page at: {webui_link}")
    except Exception as e:
        print(f"Failed to update page: {e}")

if __name__ == "__main__":
    main()
