import random
import unittest
from rbc_app import WeatherParticle


class WeatherParticleTests(unittest.TestCase):
    def test_rain_and_petals_move_and_recycle_in_resized_windows(self):
        for effect in ('rain','petals'):
            with self.subTest(effect=effect):
                p=WeatherParticle(effect,random.Random(7))
                initial=(p.x,p.y)
                for width,height in ((800,430),(580,900),(1200,600)):
                    for _ in range(500):
                        x,y=p.step(width,height)
                        self.assertTrue(-.05*width<=x<=1.05*width)
                        self.assertTrue(-.04*height<=y<=1.04*height)
                self.assertNotEqual(initial,(p.x,p.y))

    def test_petals_fall_more_slowly_than_rain(self):
        rain=WeatherParticle('rain',random.Random(12))
        petals=WeatherParticle('petals',random.Random(12))
        self.assertGreater(rain.speed,petals.speed*5)

    def test_pouring_rain_has_long_fast_streaks(self):
        for seed in range(30):
            drop=WeatherParticle('rain',random.Random(seed))
            self.assertGreaterEqual(drop.speed,16)
            self.assertLessEqual(drop.speed,28)
            self.assertGreaterEqual(drop.size,12)
            self.assertLessEqual(drop.size,24)
