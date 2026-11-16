import random
import unittest
from rbc_app import OceanDrifter


class OceanMotionTests(unittest.TestCase):
    def test_drifters_move_smoothly_and_stay_in_depth_band_after_resize(self):
        for depth in (.15,.5,.94):
            fish=OceanDrifter(depth,random.Random(17))
            start=(fish.x,fish.y)
            for width,height in ((800,900),(1200,700),(640,1000)):
                previous=None
                for tick in range(600):
                    x,y,direction=fish.step(width,height)
                    self.assertTrue(.05*width<=x<=.95*width)
                    self.assertTrue(fish.low*height<=y<=fish.high*height)
                    self.assertIn(direction,(-1,1))
                    if previous:
                        self.assertLess(abs(x-previous[0]),1.1)
                        self.assertLess(abs(y-previous[1]),.75)
                    previous=(x,y)
            self.assertNotEqual(start,(fish.x,fish.y))
