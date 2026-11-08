"""Generates synthetic payment-confirmation screenshots for testing. No real data is used."""
import io
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ExifTags

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
W, H = 720, 1280
AMOUNT_BOX = (210, 330, 510, 395)   # where the amount is drawn (x0,y0,x1,y1)
LOGO_BOX = (60, 40, 180, 160)       # avatar/logo area used for the pasted-region test


def f(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)


def base_screenshot(amount="INR 1,500.00"):
    im = Image.new("RGB", (W, H), (245, 247, 250))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 200), fill=(30, 64, 175))
    d.ellipse(LOGO_BOX, fill=(255, 255, 255))
    d.text((90, 85), "PAY", font=f(30, True), fill=(30, 64, 175))
    d.text((220, 80), "QuickPay Wallet", font=f(34, True), fill=(255, 255, 255))
    d.ellipse((310, 230, 410, 320), fill=(34, 160, 90))
    d.line((335, 275, 355, 297, 390, 252), fill=(255, 255, 255), width=8)
    d.text((W // 2, 360), amount, font=f(44, True), fill=(20, 20, 20), anchor="mm")
    d.text((W // 2, 430), "Payment Successful", font=f(28), fill=(34, 160, 90), anchor="mm")
    rows = [("Paid to", "Ravi Kumar Stores"), ("UPI ID", "ravikumar@quickpay"), ("Transaction ID", "T2611081423567890"),
            ("Date", "08 Nov 2026, 02:14 PM"), ("Bank Ref No", "6091 2345 7788"), ("Status", "Completed")]
    y = 520
    for k, v in rows:
        d.text((60, y), k, font=f(26), fill=(110, 110, 120))
        d.text((W - 60, y), v, font=f(26, True), fill=(25, 25, 30), anchor="ra")
        d.line((60, y + 52, W - 60, y + 52), fill=(225, 228, 235), width=2)
        y += 90
    d.text((W // 2, 1150), "Powered by QuickPay (demo)", font=f(22), fill=(150, 150, 160), anchor="mm")
    return im


def jpeg_roundtrip(im, q, exif=None):
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=q, **({"exif": exif} if exif else {}))
    buf.seek(0)
    out = Image.open(buf)
    out.load()
    return out


def make_exif(software=None):
    ex = Image.Exif()
    ex[0x010F], ex[0x0110] = "DemoPhone", "DP-1"
    ex[0x0132] = "2026:11:08 14:14:30"
    if software:
        ex[0x0131] = software
    return ex.tobytes()


def tamper_text(im):
    im = im.copy()
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = AMOUNT_BOX
    d.rectangle((x0 - 30, y0 - 5, x1 + 30, y1 + 5), fill=(245, 247, 250))
    d.text((W // 2 + 3, 366), "INR 15,000.00", font=f(40, True), fill=(35, 20, 20), anchor="mm")  # different size, offset & colour
    return im


def tamper_text_splice(im):
    """Amount replaced by a crop rendered elsewhere and saved at a different JPEG quality (realistic splice)."""
    im = im.copy()
    x0, y0, x1, y1 = AMOUNT_BOX
    src = Image.new("RGB", (x1 - x0 + 60, y1 - y0 + 10), (245, 247, 250))
    ImageDraw.Draw(src).text(((x1 - x0 + 60) // 2, (y1 - y0 + 10) // 2), "INR 15,000.00", font=f(44, True), fill=(20, 20, 20), anchor="mm")
    src = jpeg_roundtrip(src, 55)
    im.paste(src, (x0 - 30, y0 - 5))
    return im


def tamper_image(im):
    im = im.copy()
    rng = np.random.default_rng(7)
    x0, y0, x1, y1 = LOGO_BOX
    w, h = x1 - x0, y1 - y0
    gx = np.linspace(0, 1, w)[None, :, None]
    gy = np.linspace(0, 1, h)[:, None, None]
    patch = np.concatenate([60 + 150 * gx * np.ones((h, 1, 1)), 90 + 100 * gy * np.ones((1, w, 1)), 160 + 60 * gx * gy], axis=2)
    patch = patch + rng.normal(0, 6, patch.shape)
    im.paste(Image.fromarray(np.clip(patch, 0, 255).astype(np.uint8)), (x0, y0))
    return im


def save_jpeg(path, im, q, exif=None):
    im.save(path, "JPEG", quality=q, **({"exif": exif} if exif else {}))


def generate(out_dir):
    """Each file is written with exactly ONE final JPEG save so the intended compression history is preserved."""
    os.makedirs(out_dir, exist_ok=True)
    base = base_screenshot()
    P = lambda n: os.path.join(out_dir, n)
    # 1 normal: saved once, like a screenshot forwarded by a messaging app
    save_jpeg(P("01_normal.jpg"), base, 90, make_exif())
    # 2 text edited: first save q75 (the "original"), amount edited, saved again q92
    save_jpeg(P("02_modified_text.jpg"), tamper_text(jpeg_roundtrip(base, 75)), 92)
    # 3 image region replaced with a pasted noisy gradient
    save_jpeg(P("03_modified_image_region.jpg"), tamper_image(jpeg_roundtrip(base, 75)), 92)
    # 2b amount replaced by a spliced crop with a different compression history
    save_jpeg(P("02b_spliced_text.jpg"), tamper_text_splice(jpeg_roundtrip(base, 75)), 92)
    # 4 heavily and repeatedly compressed, no edit
    save_jpeg(P("04_compressed.jpg"), jpeg_roundtrip(jpeg_roundtrip(base, 35), 60), 40)
    # 5 PNG without EXIF
    base.save(P("05_no_exif.png"))
    # 6 edited text + editor software tag in EXIF
    save_jpeg(P("06_modified_text_editor_tag.jpg"), tamper_text(jpeg_roundtrip(base, 75)), 92, make_exif("Adobe Photoshop 25.0"))
    return {n: P(n) for n in sorted(os.listdir(out_dir)) if n[0].isdigit()}


if __name__ == "__main__":
    print(generate(os.path.join(os.path.dirname(__file__), "samples")))
