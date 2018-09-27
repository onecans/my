from django.test import TestCase
import pandas as pd
from datareader.backend.rzrq import RZRQ
from datareader.backend.fin import get_fin
from datareader.backend.se import SE
# Create your tests here.
import os


class RZRQTestCase(TestCase):
    def setUp(self):
        RZRQ.file_path = os.path.join(RZRQ.file_path, 'test')

    def test_rzrq(self):

        r = RZRQ('601600')
        df = r.df()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(len(df) > 300)


class FinFileTest(TestCase):
    def test_get_fin(self):
        get_fin('2018', 1)


class SETest(TestCase):
    def test_pe(self):
        SE().get_pe()
