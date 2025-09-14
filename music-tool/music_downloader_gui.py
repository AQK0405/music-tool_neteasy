import json
import execjs
import requests
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import os
import time
from tkinter import filedialog

class MusicDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("网易云音乐下载器")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 设置中文字体支持
        self.style = ttk.Style()
        self.style.configure("TLabel", font=('SimHei', 10))
        self.style.configure("TButton", font=('SimHei', 10))
        self.style.configure("TEntry", font=('SimHei', 10))
        
        # 音乐类型配置
        self.type_config = {
            'getLink': {
                'url': 'https://music.163.com/weapi/song/enhance/player/url/v1?csrf_token=6405ca0b9a9939b23f9fc79182969ac8',
                'i2x': {"ids":"<keyword>","level":"exhigh","encodeType":"aac","csrf_token":"6405ca0b9a9939b23f9fc79182969ac8"}
            },
            'search': {
                'url': 'https://music.163.com/weapi/cloudsearch/get/web?csrf_token=6405ca0b9a9939b23f9fc79182969ac8',
                'i2x': {"hlpretag":"<span class=\"s-fc7\">","hlposttag":"</span>","s":"<keyword>","type":"1","offset":"0","total":"true","limit":"100","csrf_token":"6405ca0b9a9939b23f9fc79182969ac8"}
            }
        }
        
        # 存储搜索结果
        self.song_list = []
        
        # 存储下载按钮引用，用于滚动时更新位置
        self.download_buttons = {}
        
        # 默认下载目录
        self.download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        
        # 创建界面
        self.create_widgets()
    
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="网易云音乐下载器", font=('SimHei', 16, 'bold'))
        title_label.pack(pady=10)
        
        # 搜索框架
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=10)
        
        # 搜索标签
        search_label = ttk.Label(search_frame, text="搜索关键词:")
        search_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # 搜索输入框
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda event: self.start_search())
        
        # 搜索按钮
        self.search_button = ttk.Button(search_frame, text="搜索", command=self.start_search)
        self.search_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 下载目录选择按钮
        self.dir_button = ttk.Button(search_frame, text="选择下载目录", command=self.choose_download_dir)
        self.dir_button.pack(side=tk.LEFT)
        
        # 下载目录显示
        self.dir_label = ttk.Label(main_frame, text=f"下载目录: {self.download_dir}", wraplength=700)
        self.dir_label.pack(anchor=tk.W, pady=(0, 10))
        
        # 结果统计
        self.stats_label = ttk.Label(main_frame, text="")
        self.stats_label.pack(anchor=tk.W, pady=(0, 10))
        
        # 创建表格框架
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建表格 - 添加选择列
        columns = ("select", "index", "name", "artist", "action")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        
        # 定义列
        self.tree.heading("select", text="选择")
        self.tree.heading("index", text="序号")
        self.tree.heading("name", text="歌曲名")
        self.tree.heading("artist", text="歌手")
        self.tree.heading("action", text="操作")
        
        # 设置列宽
        self.tree.column("select", width=60, anchor=tk.CENTER)
        self.tree.column("index", width=50, anchor=tk.CENTER)
        self.tree.column("name", width=280, anchor=tk.W)
        self.tree.column("artist", width=180, anchor=tk.W)
        self.tree.column("action", width=100, anchor=tk.CENTER)
        
        # 存储选中状态
        self.selected_items = {}
        
        # 添加选择事件
        self.tree.bind('<ButtonRelease-1>', self.on_item_click)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        # 布局表格和滚动条
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 添加滚动事件监听
        self.tree.bind('<Configure>', self.on_scroll)
        self.tree.bind('<MouseWheel>', self.on_mousewheel)
        scrollbar.bind('<Motion>', self.on_scroll)
        
        # 批量操作按钮框架
        batch_frame = ttk.Frame(main_frame)
        batch_frame.pack(fill=tk.X, pady=(10, 5))
        
        # 全选按钮
        self.select_all_btn = ttk.Button(batch_frame, text="全选", command=self.select_all)
        self.select_all_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 取消全选按钮
        self.deselect_all_btn = ttk.Button(batch_frame, text="取消全选", command=self.deselect_all)
        self.deselect_all_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 批量下载按钮
        self.batch_download_btn = ttk.Button(batch_frame, text="批量下载", command=self.start_batch_download)
        self.batch_download_btn.pack(side=tk.LEFT)
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def update_button_positions(self):
        """更新所有下载按钮的位置"""
        self.root.update_idletasks()  # 确保UI已更新
        
        for item, button in self.download_buttons.items():
            # 获取单元格的当前位置
            bbox = self.tree.bbox(item, "action")
            if bbox:  # 如果单元格可见
                x, y, width, height = bbox
                # 更新按钮位置
                button.place(x=x + (width - 60) // 2, y=y + 1, width=60, height=height - 2)
                button.lift()  # 确保按钮显示在最上层
            else:
                # 如果单元格不可见，隐藏按钮
                button.place_forget()
    
    def on_scroll(self, event=None):
        """处理滚动事件"""
        # 使用after来避免过于频繁的更新
        self.root.after(50, self.update_button_positions)
    
    def on_mousewheel(self, event):
        """处理鼠标滚轮事件"""
        # 允许使用鼠标滚轮滚动表格
        self.tree.yview_scroll(int(-1*(event.delta/120)), "units")
        # 更新按钮位置
        self.on_scroll()
    
    def on_item_click(self, event):
        """处理表格项点击事件，更新选择状态"""
        region = self.tree.identify_region(event.x, event.y)
        item = self.tree.identify_row(event.y)
        
        # 确保点击的是有效的行和选择列
        if item and region == 'cell':
            column = self.tree.identify_column(event.x)
            if column == '#1':  # 选择列
                # 切换选中状态
                is_selected = not self.selected_items.get(item, False)
                self.selected_items[item] = is_selected
                
                # 更新选择框显示
                self.tree.set(item, "select", "✓" if is_selected else "□")
    
    def select_all(self):
        """全选功能"""
        for item in self.selected_items:
            self.selected_items[item] = True
            self.tree.set(item, "select", "✓")
    
    def deselect_all(self):
        """取消全选功能"""
        for item in self.selected_items:
            self.selected_items[item] = False
            self.tree.set(item, "select", "□")
    
    def start_batch_download(self):
        """开始批量下载"""
        # 获取选中的歌曲
        selected_songs = []
        for item, is_selected in self.selected_items.items():
            if is_selected:
                # 获取行索引
                idx = int(self.tree.set(item, "index")) - 1
                if 0 <= idx < len(self.song_list):
                    song = self.song_list[idx]
                    if song.get('url'):  # 确保有下载链接
                        selected_songs.append(song)
        
        if not selected_songs:
            messagebox.showwarning("警告", "请先选择要下载的歌曲")
            return
        
        # 在新线程中执行批量下载
        threading.Thread(target=self._batch_download_thread, 
                        args=(selected_songs,), daemon=True).start()
    
    def _batch_download_thread(self, songs):
        """批量下载的线程函数"""
        total = len(songs)
        success_count = 0
        fail_count = 0
        failed_songs = []
        
        try:
            for i, song in enumerate(songs, 1):
                # 更新状态栏显示进度
                self.root.after(0, self.status_var.set, 
                               f"批量下载中: {song['name']} - {song['ar']} ({i}/{total})")
                
                try:
                    # 下载单个歌曲
                    response = requests.get(song['url'], stream=True)
                    if response.status_code != 200:
                        fail_count += 1
                        failed_songs.append(f"{song['name']} - {song['ar']} (HTTP状态码: {response.status_code})")
                        continue
                    
                    # 准备文件名
                    filename = f"{song['name']} - {song['ar']}.mp3"
                    filename = self._sanitize_filename(filename)
                    filepath = os.path.join(self.download_dir, filename)
                    
                    # 下载文件
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=1024):
                            if chunk:
                                f.write(chunk)
                    
                    success_count += 1
                    
                except Exception as e:
                    fail_count += 1
                    failed_songs.append(f"{song['name']} - {song['ar']} ({str(e)})")
            
            # 下载完成后的总结信息
            summary = f"批量下载完成！\n成功: {success_count}首\n失败: {fail_count}首"
            if failed_songs:
                summary += "\n\n失败列表:\n" + "\n".join(failed_songs)
            
            self.root.after(0, messagebox.showinfo, "批量下载完成", summary)
            self.root.after(0, self.status_var.set, "批量下载完成")
            
        except Exception as e:
            self.root.after(0, messagebox.showerror, "批量下载错误", f"批量下载失败: {str(e)}")
            self.root.after(0, self.status_var.set, "批量下载失败")
    
    def choose_download_dir(self):
        """选择下载目录"""
        directory = filedialog.askdirectory(title="选择下载目录", initialdir=self.download_dir)
        if directory:
            self.download_dir = directory
            self.dir_label.config(text=f"下载目录: {self.download_dir}")
    
    def start_search(self):
        """开始搜索音乐"""
        keyword = self.search_entry.get().strip()
        if not keyword:
            messagebox.showwarning("警告", "请输入搜索关键词")
            return
        
        # 清空之前的结果
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 禁用搜索按钮
        self.search_button.config(state=tk.DISABLED)
        self.status_var.set(f"正在搜索 '{keyword}'...")
        
        # 在新线程中执行搜索，避免UI卡顿
        threading.Thread(target=self.search_music, args=(keyword,), daemon=True).start()
    
    def get_encrypted_params(self, i2x):
        """获取加密参数"""
        try:
            with open('temp.js', mode='r', encoding='utf-8') as f:
                a = execjs.compile(f.read())
                res = a.call('main', i2x)
                return res
        except Exception as e:
            messagebox.showerror("错误", f"获取加密参数失败: {str(e)}")
            return None
    
    def make_request(self, keyword, flag):
        """发送请求获取数据"""
        try:
            # 读取cookie
            cookie = ''
            with open('cookie.txt', mode='r', encoding='utf-8') as f:
                cookie = f.read()
                
            header = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
                'content-type': 'application/x-www-form-urlencoded',
                'cookie': cookie
            }
            
            url = self.type_config[flag]['url']
            i2x = str(self.type_config[flag]['i2x']).replace('<keyword>', str(keyword))
            encrypted_params = self.get_encrypted_params(i2x)
            
            if not encrypted_params:
                return None
            
            data = {
                'params': encrypted_params.get('encText'),
                'encSecKey': encrypted_params.get('encSecKey')
            }
            
            return requests.post(url, headers=header, data=data)
        except Exception as e:
            messagebox.showerror("错误", f"发送请求失败: {str(e)}")
            return None
    
    def get_artists(self, ars):
        """提取歌手信息"""
        ar_arr = []
        for ar in ars:
            ar_arr.append(ar.get('name'))
        return '/'.join(ar_arr)
    
    def add_song_links(self, data, song_list):
        """为歌曲列表添加下载链接"""
        for song in song_list:
            for i in data:
                if i.get('id') == song.get('id'):
                    song['url'] = i.get('url')
    
    def search_music(self, keyword):
        """搜索音乐"""
        start_time = time.time()
        self.song_list = []
        song_ids = []
        
        try:
            # 搜索歌曲
            search_result = self.make_request(keyword=keyword, flag='search')
            if not search_result:
                return
            
            search_data = json.loads(search_result.text)
            
            # 处理搜索结果
            for song in search_data.get('result', {}).get('songs', []):
                song_id = song.get('id')
                name = song.get('name')
                artists = self.get_artists(song.get('ar', []))
                song_ids.append(int(song_id))
                
                temp = {
                    'id': song_id,
                    'name': name,
                    'ar': artists
                }
                self.song_list.append(temp)
            
            # 获取下载链接
            if self.song_list:
                link_data = self.make_request(keyword=song_ids, flag='getLink')
                if link_data:
                    link_json = json.loads(link_data.text)
                    self.add_song_links(link_json.get('data', []), self.song_list)
            
            end_time = time.time()
            
            # 更新UI
            self.root.after(0, self.update_search_results, end_time - start_time)
            
        except Exception as e:
            self.root.after(0, messagebox.showerror, "搜索错误", f"搜索失败: {str(e)}")
            self.root.after(0, self.search_button.config, {'state': tk.NORMAL})
            self.root.after(0, self.status_var.set, "搜索失败")
    
    def update_search_results(self, time_cost):
        """更新搜索结果UI"""
        # 显示搜索结果
        # 清空之前的按钮引用
        self.download_buttons.clear()
        
        # 清空选中状态
        self.selected_items.clear()
        
        for index, song in enumerate(self.song_list, 1):
            # 在表格中插入行（包含选择框）
            item = self.tree.insert('', tk.END, values=("□", index, song['name'], song['ar'], "下载"))
            
            # 创建下载按钮
            download_btn = ttk.Button(self.tree, text="下载", width=8,
                                     command=lambda s=song: self.download_song(s))
            
            # 禁用没有下载链接的按钮
            if not song.get('url'):
                download_btn.config(state=tk.DISABLED)
            
            # 将按钮放置在单元格中
            self.tree.set(item, "action", "")  # 清空文本
            
            # 存储按钮引用和选中状态
            self.download_buttons[item] = download_btn
            self.selected_items[item] = False
        
        # 触发一次滚动事件以更新所有按钮位置
        self.update_button_positions()
        
        # 更新统计信息
        self.stats_label.config(text=f"找到 {len(self.song_list)} 首歌曲，用时 {time_cost:.2f} 秒")
        
        # 恢复搜索按钮状态
        self.search_button.config(state=tk.NORMAL)
        self.status_var.set("搜索完成")
    
    def download_song(self, song):
        """下载歌曲"""
        if not song.get('url'):
            messagebox.showwarning("警告", f"无法下载 '{song['name']}' - 没有可用的下载链接")
            return
        
        # 在新线程中执行下载
        threading.Thread(target=self._download_song_thread, args=(song,), daemon=True).start()
    
    def _download_song_thread(self, song):
        """下载歌曲的线程函数"""
        try:
            # 更新状态栏
            self.root.after(0, self.status_var.set, f"正在下载: {song['name']} - {song['ar']}")
            
            # 发送下载请求
            response = requests.get(song['url'], stream=True)
            if response.status_code != 200:
                self.root.after(0, messagebox.showerror, "下载失败", f"无法下载 '{song['name']}' - HTTP状态码: {response.status_code}")
                self.root.after(0, self.status_var.set, "下载失败")
                return
            
            # 准备文件名（处理特殊字符）
            filename = f"{song['name']} - {song['ar']}.mp3"
            filename = self._sanitize_filename(filename)
            filepath = os.path.join(self.download_dir, filename)
            
            # 下载文件
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # 更新下载进度
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            self.root.after(0, self.status_var.set, 
                                           f"正在下载: {song['name']} - {song['ar']} ({progress:.1f}%)")
            
            # 下载完成
            self.root.after(0, self.status_var.set, "下载完成")
            self.root.after(0, messagebox.showinfo, "下载完成", 
                           f"歌曲 '{song['name']} - {song['ar']}' 已下载到:\n{filepath}")
            
        except Exception as e:
            self.root.after(0, messagebox.showerror, "下载错误", f"下载失败: {str(e)}")
            self.root.after(0, self.status_var.set, "下载失败")
    
    def _sanitize_filename(self, filename):
        """清理文件名中的特殊字符"""
        # 使用列表定义不允许的字符，避免字符串转义问题
        invalid_chars = ['<', '>', '"', '/', '\\', '|', '?', '*', '\n', '\t', ':']
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename

if __name__ == "__main__":
    # 创建主窗口
    root = tk.Tk()
    
    # 确保中文显示正常
    try:
        # 设置中文字体
        root.option_add("*Font", "SimHei 10")
    except:
        pass  # 如果字体不可用，使用默认字体
    
    # 创建应用实例
    app = MusicDownloaderGUI(root)
    
    # 启动主循环
    root.mainloop()