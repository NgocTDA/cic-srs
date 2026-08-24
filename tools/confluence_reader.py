#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
confluence_reader.py - Công cụ độc lập đọc nội dung Confluence trực tiếp qua REST API
và chuyển đổi sang Markdown chuẩn (sử dụng BeautifulSoup4 để xử lý triệt để table lồng nhau và macros).
"""

import os
import sys
import re
import json
import ssl
import argparse
import urllib.request
import urllib.error
import urllib.parse
from bs4 import BeautifulSoup, NavigableString, Tag

for _stream in (sys.stdout, sys.stderr):
    if _stream.encoding and _stream.encoding.lower() != 'utf-8':
        try:
            _stream.reconfigure(encoding='utf-8')
        except Exception:
            pass


def load_env(env_path=None):
    """Đọc file .env đơn giản."""
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
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k not in env_vars:
                            env_vars[k] = v
            break
    return env_vars


def convert_node(node, in_table_cell=False):
    if isinstance(node, NavigableString):
        text = str(node)
        if in_table_cell:
            text = text.replace('\n', ' ').replace('|', '\\|')
        return text

    if not isinstance(node, Tag):
        return ""

    tag_name = node.name.lower()

    if tag_name == 'ac:structured-macro':
        macro_name = node.get('ac:name', '').lower()
        body = node.find('ac:rich-text-body')
        body_md = "".join(convert_node(c, in_table_cell) for c in body.children).strip() if body else ""
        
        params = {}
        for p in node.find_all('ac:parameter', recursive=False):
            p_name = p.get('ac:name', 'default')
            params[p_name] = p.get_text().strip()

        if macro_name in ['info', 'tip', 'note', 'warning', 'expand']:
            alert_map = {'info': 'NOTE', 'tip': 'TIP', 'note': 'IMPORTANT', 'warning': 'WARNING', 'expand': 'NOTE'}
            alert_type = alert_map.get(macro_name, 'NOTE')
            title = params.get('title', '')
            lines = body_md.split('\n')
            res = f"\n\n> [!{alert_type}]"
            if title:
                res += f"\n> **{title}**"
            for l in lines:
                if l.strip():
                    res += f"\n> {l}"
            return res + "\n\n"
        elif macro_name == 'code':
            lang = params.get('language', '')
            plain = node.find('ac:plain-text-body')
            code_text = plain.get_text() if plain else body_md
            return f"\n\n```{lang}\n{code_text}\n```\n\n"
        elif macro_name == 'status':
            title = params.get('title', body_md)
            return f" `[{title}]` "
        elif macro_name == 'children':
            return "\n\n*(Danh sách trang con)*\n\n"
        else:
            return body_md

    if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        lvl = int(tag_name[1])
        inner = "".join(convert_node(c, in_table_cell) for c in node.children).strip()
        return f"\n\n{'#' * lvl} {inner}\n\n"

    if tag_name == 'p':
        inner = "".join(convert_node(c, in_table_cell) for c in node.children).strip()
        if not inner:
            return ""
        if in_table_cell:
            return inner + "<br>"
        return f"\n\n{inner}\n\n"

    if tag_name == 'br':
        if in_table_cell:
            return "<br>"
        return "\n"

    if tag_name in ['strong', 'b']:
        inner = "".join(convert_node(c, in_table_cell) for c in node.children)
        if not inner.strip():
            return ""
        return f"**{inner}**"

    if tag_name in ['em', 'i']:
        inner = "".join(convert_node(c, in_table_cell) for c in node.children)
        if not inner.strip():
            return ""
        return f"*{inner}*"

    if tag_name == 'code':
        inner = node.get_text()
        return f"`{inner}`"

    if tag_name == 'a':
        href = node.get('href', '')
        inner = "".join(convert_node(c, in_table_cell) for c in node.children).strip() or href
        return f"[{inner}]({href})"

    if tag_name == 'ri:attachment':
        filename = node.get('ri:filename', '')
        return f" [Attachment: {filename}] "

    if tag_name == 'ac:image':
        # <ac:image><ri:url ri:value="..."/></ac:image> = ảnh dán từ URL ngoài,
        # không phải file đính kèm — không có handler riêng trước đây nên bị mất trắng.
        ri_url = node.find('ri:url', recursive=False)
        if ri_url is not None:
            url_value = ri_url.get('ri:value', '')
            alt = node.get('ac:alt', '') or node.get('ac:title', '')
            if url_value:
                return f"![{alt}]({url_value})"
            return " [Ảnh URL ngoài không xác định] "
        # Trường hợp ri:attachment: giữ hành vi cũ, đệ quy xuống handler ri:attachment ở trên.
        return "".join(convert_node(c, in_table_cell) for c in node.children)

    if tag_name == 'ac:link':
        # <ac:link><ri:page ri:content-title="..."/></ac:link> = liên kết nội bộ Confluence,
        # không có href để giữ nên trước đây mất luôn cả text hiển thị.
        ri_page = node.find('ri:page', recursive=False)
        if ri_page is not None:
            body = node.find('ac:link-body', recursive=False) or node.find('ac:plain-text-link-body', recursive=False)
            label = "".join(convert_node(c, in_table_cell) for c in body.children).strip() if body else ""
            title = ri_page.get('ri:content-title', '')
            display = label or title
            return f" [Liên kết nội bộ: {display}] " if display else ""
        return "".join(convert_node(c, in_table_cell) for c in node.children)

    if tag_name == 'ul':
        items = []
        for li in node.find_all('li', recursive=False):
            li_text = "".join(convert_node(c, in_table_cell) for c in li.children).strip()
            if in_table_cell:
                items.append(f"• {li_text}")
            else:
                items.append(f"- {li_text}")
        if in_table_cell:
            return "<br>".join(items)
        return "\n" + "\n".join(items) + "\n"

    if tag_name == 'ol':
        items = []
        for i, li in enumerate(node.find_all('li', recursive=False), 1):
            li_text = "".join(convert_node(c, in_table_cell) for c in li.children).strip()
            if in_table_cell:
                items.append(f"{i}. {li_text}")
            else:
                items.append(f"{i}. {li_text}")
        if in_table_cell:
            return "<br>".join(items)
        return "\n" + "\n".join(items) + "\n"

    if tag_name == 'table':
        if in_table_cell:
            inner_text = node.get_text(separator=' | ', strip=True)
            return f" [Table: {inner_text}] "
        
        def _rows_from(container):
            rs = []
            for tr in container.find_all('tr', recursive=False):
                row_cells = []
                for cell in tr.find_all(['th', 'td'], recursive=False):
                    cell_content = "".join(convert_node(c, in_table_cell=True) for c in cell.children).strip()
                    row_cells.append(cell_content)
                if row_cells:
                    rs.append(row_cells)
            return rs

        # Gộp tr là con trực tiếp của <table> VÀ tr nằm trong <thead>/<tbody>/<tfoot> —
        # trước đây chỉ quét cái sau khi cái trước rỗng, nên bảng có cả hai kiểu bị mất phần thân.
        rows = _rows_from(node)
        for section in node.find_all(['thead', 'tbody', 'tfoot'], recursive=False):
            rows.extend(_rows_from(section))

        if not rows:
            return ""

        max_cols = max(len(r) for r in rows)
        if max_cols == 0:
            return ""

        table_md = []
        header = rows[0] + [''] * (max_cols - len(rows[0]))
        table_md.append('| ' + ' | '.join(header) + ' |')
        table_md.append('| ' + ' | '.join(['---'] * max_cols) + ' |')
        for r in rows[1:]:
            norm_r = r + [''] * (max_cols - len(r))
            table_md.append('| ' + ' | '.join(norm_r) + ' |')

        return "\n\n" + "\n".join(table_md) + "\n\n"

    return "".join(convert_node(c, in_table_cell) for c in node.children)


class ConfluenceReader:
    def __init__(self, base_url=None, token=None, insecure_http=True, verify_tls=True):
        env = load_env()
        self.base_url = (base_url or env.get('CONFLUENCE_URL', 'http://10.16.16.242:8090/')).rstrip('/')
        self.fallback_url = env.get('CONFLUENCE_FALLBACK_URL', 'https://cic.ntda.io.vn').rstrip('/')
        self.token = token or env.get('CONFLUENCE_TOKEN', '')
        self.space_key = env.get('CONFLUENCE_SPACE', 'CIC')
        self.insecure_http = insecure_http
        self.verify_tls = verify_tls

        self.ctx = ssl.create_default_context()
        if not self.verify_tls:
            self.ctx.check_hostname = False
            self.ctx.verify_mode = ssl.CERT_NONE

    def _get_headers(self):
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Antigravity-Confluence-Reader/1.0'
        }
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers

    def _call_api(self, endpoint):
        urls_to_try = [f"{self.base_url}{endpoint}"]
        if self.fallback_url and self.fallback_url != self.base_url:
            urls_to_try.append(f"{self.fallback_url}{endpoint}")

        last_err = None
        for u in urls_to_try:
            try:
                req = urllib.request.Request(u, headers=self._get_headers())
                with urllib.request.urlopen(req, timeout=10, context=self.ctx) as resp:
                    return json.loads(resp.read().decode('utf-8'))
            except Exception as e:
                last_err = e
                continue
        raise last_err

    def extract_page_id(self, page_input):
        page_input = str(page_input).strip()
        if page_input.isdigit():
            return page_input
        match = re.search(r'pageId=(\d+)', page_input)
        if match:
            return match.group(1)
        match = re.search(r'/pages/(\d+)', page_input)
        if match:
            return match.group(1)
        return page_input

    def get_page(self, page_id_or_url):
        page_id = self.extract_page_id(page_id_or_url)
        endpoint = f"/rest/api/content/{page_id}?expand=body.storage,version,title,ancestors,children.page,space"
        data = self._call_api(endpoint)
        
        title = data.get('title', '')
        version = data.get('version', {}).get('number', 1)
        by_user = data.get('version', {}).get('by', {}).get('displayName', '')
        created_date = data.get('version', {}).get('when', '')
        space = data.get('space', {}).get('key', '')
        storage_html = data.get('body', {}).get('storage', {}).get('value', '')

        soup = BeautifulSoup(storage_html, 'html.parser')
        markdown_body = convert_node(soup)
        markdown_body = re.sub(r'\n{3,}', '\n\n', markdown_body).strip()

        children = []
        for child in data.get('children', {}).get('page', {}).get('results', []):
            children.append({
                'id': child.get('id'),
                'title': child.get('title')
            })

        ancestors = []
        for anc in data.get('ancestors', []):
            ancestors.append({
                'id': anc.get('id'),
                'title': anc.get('title')
            })

        return {
            'id': page_id,
            'title': title,
            'version': version,
            'author': by_user,
            'date': created_date,
            'space': space,
            'ancestors': ancestors,
            'children': children,
            'markdown': markdown_body,
            'raw_storage': storage_html
        }

    def get_attachments(self, page_id):
        endpoint = f"/rest/api/content/{page_id}/child/attachment?expand=version"
        data = self._call_api(endpoint)
        return data.get('results', [])

    def download_attachment(self, attachment, dest_dir):
        download_uri = attachment.get('_links', {}).get('download', '')
        if not download_uri:
            return None
        title = attachment.get('title', '')
        url = f"{self.base_url}{download_uri}"
        
        os.makedirs(dest_dir, exist_ok=True)
        out_path = os.path.join(dest_dir, title)
        
        try:
            req = urllib.request.Request(url, headers=self._get_headers())
            with urllib.request.urlopen(req, timeout=30, context=self.ctx) as resp:
                with open(out_path, 'wb') as f:
                    f.write(resp.read())
            return title
        except Exception as e:
            print(f"[!] Lỗi tải ảnh {title}: {e}")
            return None


def main():
    parser = argparse.ArgumentParser(description="Confluence Page Reader - Tải và chuyển đổi trang Confluence sang Markdown")
    parser.add_argument("page", help="Page ID hoặc URL của trang Confluence")
    parser.add_argument("-o", "--output", help="Đường dẫn file .md đầu ra (mặc định in ra console hoặc lưu file)")
    parser.add_argument("--save", action="store_true", help="Tự động lưu ra file <pageId>_<Title>.md tại thư mục confluence_pages/")
    parser.add_argument("--json", action="store_true", help="Xuất định dạng JSON")
    parser.add_argument("--token", help="Confluence Personal Access Token (ghi đè .env)")
    parser.add_argument("--url", help="Confluence Base URL (ghi đè .env)")
    parser.add_argument("--insecure-tls", action="store_true",
                        help="Bỏ kiểm chứng chứng chỉ TLS (chỉ dùng khi server nội bộ dùng self-signed cert)")

    parser.add_argument("--srs-func", help="Mã chức năng (VD: FUNC-KKN-001) để tự động pull các trang con, gán mã FEAT và gộp chung vào một file")
    parser.add_argument("--subpage-strategy", choices=['ask', 'flatten', 'embed', 'abort'], default='ask', 
                        help="Chiến lược xử lý khi một trang FEAT lại có trang con (ask/flatten/embed/abort)")

    args = parser.parse_args()

    reader = ConfluenceReader(base_url=args.url, token=args.token, verify_tls=not args.insecure_tls)
    try:
        print(f"[*] Đang tải dữ liệu Confluence cho: {args.page}...")
        page_info = reader.get_page(args.page)
        print(f"[✓] Đã tải thành công: [{page_info['id']}] {page_info['title']} (v{page_info['version']})")
        
        if args.json:
            print(json.dumps(page_info, ensure_ascii=False, indent=2))
            return

        out_path = args.output
        if not out_path and args.save:
            clean_title = re.sub(r'[\\/*?:"<>|]', '_', page_info['title'])
            save_dir = os.path.join(os.getcwd(), 'confluence_pages')
            os.makedirs(save_dir, exist_ok=True)
            out_path = os.path.join(save_dir, f"{page_info['id']}_{clean_title}.md")

        if args.srs_func:
            base_feat = args.srs_func.replace("FUNC-", "FEAT-")
            print(f"[*] Chế độ --srs-func: Phát hiện {len(page_info['children'])} trang con cấp 1. Đang áp dụng chiến lược đệ quy: {args.subpage_strategy}")
            
            out_dir = os.path.dirname(os.path.abspath(out_path)) if out_path else os.getcwd()
            assets_dir = os.path.join(out_dir, 'assets')
            
            combined_md = f"# Chức năng [{args.srs_func}] {page_info['title']}\n\n> Trích xuất tự động từ Confluence ID: {page_info['id']}\n\n"
            combined_md += "## Danh sách tính năng\n\n"
            
            feat_idx = 1

            def _rename_asset(dest_dir, dl_title, f_code):
                """Đổi tên ảnh vừa tải về theo mã FEAT, tự tránh trùng tên và không crash cả batch."""
                ext = os.path.splitext(dl_title)[1]
                clean_dl = re.sub(r'[^a-zA-Z0-9_\-]', '', os.path.splitext(dl_title)[0])
                base_name = f"{f_code}_{clean_dl}{ext}"
                src = os.path.join(dest_dir, dl_title)
                candidate = base_name
                n = 1
                while os.path.exists(os.path.join(dest_dir, candidate)) and candidate != dl_title:
                    n += 1
                    candidate = f"{f_code}_{clean_dl}_{n}{ext}"
                dst = os.path.join(dest_dir, candidate)
                try:
                    os.rename(src, dst)
                    return candidate
                except OSError as e:
                    print(f"[!] Lỗi đổi tên ảnh {dl_title} -> {candidate}: {e}")
                    return None

            def replace_attachments(md_text, p_id, f_code):
                if "[Attachment:" not in md_text:
                    return md_text
                attachments = reader.get_attachments(p_id)
                for att in attachments:
                    title = att.get('title', '')
                    if f"[Attachment: {title}]" in md_text:
                        dl_title = reader.download_attachment(att, assets_dir)
                        if dl_title:
                            new_name = _rename_asset(assets_dir, dl_title, f_code)
                            if new_name is None:
                                continue
                            safe_name = urllib.parse.quote(new_name)
                            md_text = md_text.replace(f" [Attachment: {title}] ", f"\n\n![](assets/{safe_name})\n\n")
                            md_text = md_text.replace(f"[Attachment: {title}]", f"![](assets/{safe_name})")
                return md_text

            def fetch_embedded(meta, depth, f_code):
                p = reader.get_page(meta['id'])
                md = replace_attachments(p['markdown'], meta['id'], f_code)
                res = f"\n\n{'#' * depth} {p['title']}\n\n{md}"
                for gc in p['children']:
                    res += fetch_embedded(gc, depth + 1, f_code)
                return res

            original_strategy = args.subpage_strategy

            def process_page(meta, current_strategy):
                nonlocal feat_idx
                child_page = reader.get_page(meta['id'])
                has_gc = len(child_page['children']) > 0

                strat = current_strategy
                if has_gc and strat == 'ask':
                    print(f"\n[?] Phát hiện trang '{child_page['title']}' (ID: {child_page['id']}) có {len(child_page['children'])} trang con.")
                    print("Bạn muốn xử lý các trang con này như thế nào?")
                    print("  [1] Abort (Dừng lại để sửa trên Confluence)")
                    print("  [2] Flatten (Chuyển trang con thành các FEAT ngang hàng tiếp theo)")
                    print("  [3] Embed (Nhúng nội dung trang con vào làm mục con của FEAT này)")
                    while True:
                        choice = input("Lựa chọn của bạn (1/2/3): ").strip()
                        if choice == '1': strat = 'abort'; break
                        elif choice == '2': strat = 'flatten'; break
                        elif choice == '3': strat = 'embed'; break
                
                if strat == 'abort' and has_gc:
                    print("Đã hủy quá trình theo yêu cầu của người dùng.")
                    sys.exit(1)
                
                feat_code = f"{base_feat}-{feat_idx:02d}"
                feat_idx += 1
                
                print(f"  -> Đang xử lý {meta['id']} thành {feat_code} (Chiến lược: {strat})...")
                
                child_md = replace_attachments(child_page['markdown'], meta['id'], feat_code)
                features_md = ""
                
                if not has_gc or strat == 'flatten':
                    features_md += f"### {feat_code}. {child_page['title']}\n\n{child_md}\n\n---\n\n"
                    if has_gc:
                        for gc in child_page['children']:
                            # Truyền lại original_strategy (không phải strat đã resolve ở cấp
                            # này) để mỗi cấp có trang con riêng đều được hỏi lại khi mode gốc là 'ask'.
                            features_md += process_page(gc, original_strategy)
                elif strat == 'embed':
                    combined = child_md
                    for gc in child_page['children']:
                        combined += fetch_embedded(gc, 4, feat_code)
                    features_md += f"### {feat_code}. {child_page['title']}\n\n{combined}\n\n---\n\n"

                return features_md

            for child_meta in page_info['children']:
                combined_md += process_page(child_meta, original_strategy)

            if out_path:
                with open(out_path, 'w', encoding='utf-8') as f:
                    f.write(combined_md)
                print(f"[✓] Đã lưu nội dung tổng hợp sang file: {out_path}")
            else:
                print("\n" + "="*50 + " NỘI DUNG MARKDOWN " + "="*50)
                print(combined_md)
                print("="*120 + "\n")
            return

        # Regular processing without --srs-func
        header_md = f"""# {page_info['title']}

> **Confluence ID:** `{page_info['id']}` | **Space:** `{page_info['space']}` | **Version:** `v{page_info['version']}`  
> **Người cập nhật:** {page_info['author']} | **Ngày:** {page_info['date']}

---

"""
        full_md = header_md + page_info['markdown']

        if page_info['children']:
            full_md += "\n\n---\n### Danh sách trang con trực thuộc:\n"
            for c in page_info['children']:
                full_md += f"- [{c['title']}](pageId={c['id']}) (ID: `{c['id']}`)\n"

        if out_path:
            out_dir = os.path.dirname(os.path.abspath(out_path))
            assets_dir = os.path.join(out_dir, 'assets')
            
            if "[Attachment:" in full_md:
                print(f"[*] Tìm thấy ảnh đính kèm. Đang tải về thư mục assets/...")
                attachments = reader.get_attachments(page_info['id'])
                for att in attachments:
                    title = att.get('title', '')
                    if f"[Attachment: {title}]" in full_md:
                        dl_title = reader.download_attachment(att, assets_dir)
                        if dl_title:
                            safe_title = urllib.parse.quote(dl_title)
                            full_md = full_md.replace(f" [Attachment: {title}] ", f"\n\n![](assets/{safe_title})\n\n")
                            full_md = full_md.replace(f"[Attachment: {title}]", f"![](assets/{safe_title})")

            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(full_md)
            print(f"[✓] Đã lưu nội dung sang file: {out_path}")
        else:
            print("\n" + "="*50 + " NỘI DUNG MARKDOWN " + "="*50)
            print(full_md)
            print("="*120 + "\n")

    except Exception as e:
        print(f"[!] Lỗi khi đọc Confluence: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
