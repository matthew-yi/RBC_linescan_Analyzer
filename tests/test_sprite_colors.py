import unittest
from pathlib import Path
from PIL import Image
from rbc_app import clean_sprite_colors, resize_sprite


def pixels(image):
    return image.get_flattened_data() if hasattr(image,'get_flattened_data') else image.getdata()


class SpriteColorTests(unittest.TestCase):
    def test_transparent_magenta_does_not_tint_visible_pixels(self):
        sprite=Image.new('RGBA',(20,20),(255,0,255,0))
        for y in range(5,15):
            for x in range(5,15):
                sprite.putpixel((x,y),(192,204,210,255))
        result=resize_sprite(sprite,96)
        self.assertEqual({p for p in pixels(result) if p[3]}, {(192,204,210,255)})

    def test_all_four_mammals_preserve_their_source_palette(self):
        path=Path(__file__).resolve().parents[1]/'app/assets/ocean_mammals_flat.png'
        with Image.open(path) as image:
            sheet=clean_sprite_colors(image,remove_magenta=True)
        for row in range(4):
            with self.subTest(species=('dolphin','orca','humpback','beluga')[row]):
                frame=sheet.crop((0,row*sheet.height//4,sheet.width//4,(row+1)*sheet.height//4))
                frame=frame.crop(frame.getbbox())
                palette={p for p in pixels(frame) if p[3]}
                for direction in (False,True):
                    rendered=resize_sprite(frame,96,mirrored=direction)
                    visible={p for p in pixels(rendered) if p[3]}
                    self.assertTrue(visible)
                    self.assertTrue(visible<=palette)
                    self.assertFalse(any(r>g+32 and b>g+32 for r,g,b,a in visible))
