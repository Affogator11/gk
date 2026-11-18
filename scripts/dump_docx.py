from docx import Document
import glob
p = sorted(glob.glob(r"D:\文件\有趣的游戏\zujuan\\out\\*.docx"))[-1]
d = Document(p)
ps = [x.text for x in d.paragraphs]
print("paragraphs:", len(ps))
print("--- first 30 ---")
for t in ps[:30]:
    print(repr(t[:90]))
print("--- answers page ---")
i = next(i for i, t in enumerate(ps) if "参考答案" in t)
for t in ps[i:i + 8]:
    print(repr(t[:90]))
print("--- tail ---")
for t in ps[-3:]:
    print(repr(t[:90]))
