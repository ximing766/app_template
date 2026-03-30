from PIL import Image, ImageSequence
with Image.open(r"e:\Work\Python\app_template\assets\images\demo.gif") as im:
    frames = [f.copy().convert('RGB').resize((800, int(f.height * 800 / f.width)), Image.LANCZOS).convert('P', palette=Image.ADAPTIVE, colors=128) 
              for i, f in enumerate(ImageSequence.Iterator(im)) if i % 2 == 0]
    frames[0].save(r"e:\Work\Python\app_template\assets\images\demo_github.gif", save_all=True, append_images=frames[1:], optimize=True, duration=im.info.get('duration', 100) * 2, loop=0)
