#!/usr/bin/env python3
"""
譌･譛ｬ蟶ょｴ蜈ｨ驫俶氛繝・け繝九き繝ｫ繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ繧ｷ繧ｹ繝・Β v3.0 - Multi-Plan Edition
笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏・
縲・繝励Λ繝ｳ蟇ｾ蠢・+ 谿ｵ髫守噪繝ｪ繝ｪ繝ｼ繧ｹ險ｭ險医・

笆 繝ｪ繝ｪ繝ｼ繧ｹ繝ｭ繝ｼ繝峨・繝・・
  Phase 1: 證ｫ螳夂┌蜆溽沿・・LAN_MODE=free_beta・・
    - 蜈ｨ64莉ｶ繧辿TML繝ｬ繝昴・繝亥喧縺励※ GitHub Pages 縺ｧ蜈ｬ髢・
    - Slack/Discord縺ｫ縺ｯ驕ｸ謚・莉ｶ縺ｮ縺ｿ騾夂衍・井ｸｭ菴催怜､壽ｧ俶ｧ謌ｦ逡･・・
    - 隱崎ｨｼ縺ｪ縺励∬ｪｰ縺ｧ繧ゅい繧ｯ繧ｻ繧ｹ蜿ｯ閭ｽ

  Phase 2: 繝吶・繧ｷ繝・け蛻・屬・・LAN_MODE=basic・・
    - 辟｡蜆溽沿・壻ｸｭ菴・莉ｶ縺ｮ縺ｿ騾夂衍縲？TML繝ｪ繝ｳ繧ｯ縺ｪ縺・
    - 繝吶・繧ｷ繝・け・壼・莉ｶHTML・亥ｽ捺律蛻・・縺ｿ・・
    - 邁｡譏楢ｪ崎ｨｼ蟆主・

  Phase 3: 繝励Ξ繝溘い繝螳溯｣・ｼ・LAN_MODE=premium・・
    - 30譌･蛻・い繝ｼ繧ｫ繧､繝・+ 蜷・釜譟・メ繝｣繝ｼ繝育函謌・
    - Stripe騾｣謳ｺ繝ｻ隱崎ｨｼ蠑ｷ蛹・

笆 謚陦薙せ繧ｿ繝・け・・finance縺ｮ縺ｿ・・
  縲蝉ｾ｡譬ｼ繝ｻ蜃ｺ譚･鬮倥ョ繝ｼ繧ｿ・・istory・峨°繧芽ｨ育ｮ励・
    - 繝懊Μ繝ｳ繧ｸ繝｣繝ｼ繝舌Φ繝・(BB%b / 繝舌Φ繝牙ｹ・
    - 蜃ｺ譚･鬮伜・譫・(蜑肴律豈斐・30譌･蟷ｳ蝮・ｯ・
    - OBV (繧ｪ繝ｳ繝ｻ繝舌Λ繝ｳ繧ｹ繝ｻ繝懊Μ繝･繝ｼ繝) + 繝医Ξ繝ｳ繝・
    - VWAP霑台ｼｼ蛟､ (譌･雜ｳ邨ょ､繝吶・繧ｹ)
    - SMA 25 / 75 / 200 + 遘ｻ蜍募ｹｳ蝮・ｹ夜屬邇・
    - 荳逶ｮ蝮・｡｡陦ｨ (霆｢謠帷ｷ壹・蝓ｺ貅也ｷ壹・蜈郁｡後せ繝代Φ髮ｲ繝ｻ驕・｡後せ繝代Φ)
    - MA200荳頑・繝医Ξ繝ｳ繝牙愛螳・
    - 蠎募､200譌･邱壹け繝ｭ繧ｹ / MA50/100 繧ｴ繝ｼ繝ｫ繝・Φ繧ｯ繝ｭ繧ｹ

  縲腎icker.info・育ｵｱ險医ョ繝ｼ繧ｿ・峨°繧牙叙蠕励・
    - 菫｡逕ｨ蛟咲紫 / Short Ratio / Short % of Float・井ｸｻ縺ｫ邀ｳ蝗ｽ譬ｪ・・

  縲千ｷ丞粋繧ｹ繧ｳ繧｢繝ｪ繝ｳ繧ｰ縲・
    - 0縲・00轤ｹ縺ｮ轤ｹ謨ｰ蛹厄ｼ磯・轤ｹ縺ｯSCORE_WEIGHTS縺ｧ邂｡逅・ｼ・
笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏≫煤笏・
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import requests
import json
import os
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')
import jpholiday
import sys


# 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
#  螳壽焚螳夂ｾｩ
# 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
BB_PERIOD        = 20       # 繝懊Μ繝ｳ繧ｸ繝｣繝ｼ繝舌Φ繝画悄髢・
BB_STD           = 2.0      # 繝懊Μ繝ｳ繧ｸ繝｣繝ｼ繝舌Φ繝・讓呎ｺ門￥蟾ｮ蛟咲紫
OBV_TREND_DAYS   = 10       # OBV 繝医Ξ繝ｳ繝牙愛螳壽悄髢・
ICHIMOKU_CONV    = 9        # 荳逶ｮ蝮・｡｡陦ｨ 霆｢謠帷ｷ壽悄髢・
ICHIMOKU_BASE    = 26       # 荳逶ｮ蝮・｡｡陦ｨ 蝓ｺ貅也ｷ壽悄髢・
ICHIMOKU_SPAN2   = 52       # 荳逶ｮ蝮・｡｡陦ｨ 蜈郁｡後せ繝代Φ2譛滄俣
ICHIMOKU_LAG     = 26       # 荳逶ｮ蝮・｡｡陦ｨ 驕・｡後せ繝代Φ縺壹ｌ
MA_SHORT         = 25       # 遏ｭ譛櫪A・域律譛ｬ譬ｪ讓呎ｺ厄ｼ・
MA_MID           = 75       # 荳ｭ譛櫪A・域律譛ｬ譬ｪ讓呎ｺ厄ｼ・
MA_LONG          = 200      # 髟ｷ譛櫪A
SCORE_WEIGHTS = {            # 邱丞粋繧ｹ繧ｳ繧｢驟咲せ・亥粋險・00轤ｹ・・
    'ma_trend'       : 15,   # MA200荳頑・
    'golden_cross'   : 10,   # 繧ｴ繝ｼ繝ｫ繝・Φ繧ｯ繝ｭ繧ｹ
    'bottom_cross'   : 10,   # 蠎募､繧ｯ繝ｭ繧ｹ
    'bb_signal'      : 15,   # BB菴咲ｽｮ (蜿咲匱 or 繝悶Ξ繧､繧ｯ繧｢繧ｦ繝・
    'obv_trend'      : 10,   # OBV荳頑・繝医Ξ繝ｳ繝・
    'ichimoku'       : 20,   # 荳逶ｮ蝮・｡｡陦ｨ (髮ｲ荳翫・螂ｽ霆｢)
    'volume_surge'   : 10,   # 蜃ｺ譚･鬮俶･蠅・
    'short_squeeze'  : 10,   # 菫｡逕ｨ蛟咲紫繧ｹ繧ｳ繧｢
}


class TechnicalIndicators:
    """
    繝・け繝九き繝ｫ謖・ｨ呵ｨ育ｮ励け繝ｩ繧ｹ・・finance繝・・繧ｿ縺ｮ縺ｿ縺ｧ螳檎ｵ撰ｼ・
    蜷・Γ繧ｽ繝・ラ縺ｯpd.DataFrame繧貞女縺大叙繧翫∝・繧定ｿｽ蜉縺励※霑斐☆縲・
    """

    # 笏笏 繝懊Μ繝ｳ繧ｸ繝｣繝ｼ繝舌Φ繝・笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    @staticmethod
    def bollinger_bands(data: pd.DataFrame,
                        period: int = BB_PERIOD,
                        std_dev: float = BB_STD) -> pd.DataFrame:
        """
        繝懊Μ繝ｳ繧ｸ繝｣繝ｼ繝舌Φ繝峨→ %b繝ｻ繝舌Φ繝牙ｹ・ｒ險育ｮ・

        霑ｽ蜉蛻・
          BB_Middle : 荳ｭ螟ｮ邱・(SMA)
          BB_Upper  : 繧｢繝・ヱ繝ｼ繝舌Φ繝・
          BB_Lower  : 繝ｭ繝ｯ繝ｼ繝舌Φ繝・
          BB_Pct_B  : %b = (邨ょ､ - Lower) / (Upper - Lower)
                      0莉･荳・= 荳矩剞蜑ｲ繧鯉ｼ亥｣ｲ繧峨ｌ縺吶℃ / 蜿咲匱蛟呵｣懶ｼ・
                      1莉･荳・= 荳企剞遯∫ｴ・亥ｼｷ縺・ヶ繝ｬ繧､繧ｯ繧｢繧ｦ繝亥呵｣懶ｼ・
          BB_Width  : 繝舌Φ繝牙ｹ・= (Upper - Lower) / Middle・医せ繧ｯ繧､繝ｼ繧ｺ讀懃衍・・
        """
        df = data.copy()
        close = df['Close']
        df['BB_Middle'] = close.rolling(period).mean()
        std = close.rolling(period).std()
        df['BB_Upper'] = df['BB_Middle'] + std_dev * std
        df['BB_Lower'] = df['BB_Middle'] - std_dev * std
        band_range = df['BB_Upper'] - df['BB_Lower']
        df['BB_Pct_B'] = (close - df['BB_Lower']) / band_range.replace(0, np.nan)
        df['BB_Width'] = band_range / df['BB_Middle'].replace(0, np.nan)
        return df

    # 笏笏 OBV・医が繝ｳ繝ｻ繝舌Λ繝ｳ繧ｹ繝ｻ繝懊Μ繝･繝ｼ繝・俄楳笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    @staticmethod
    def obv(data: pd.DataFrame, trend_days: int = OBV_TREND_DAYS) -> pd.DataFrame:
        """
        OBV縺ｨ縺昴・繝医Ξ繝ｳ繝会ｼ井ｸ頑・/荳矩剄・峨ｒ險育ｮ・

        霑ｽ蜉蛻・
          OBV             :邏ｯ遨弘BV蛟､
          OBV_SMA         : OBV縺ｮ遏ｭ譛溽ｧｻ蜍募ｹｳ蝮・
          OBV_Trend_Up    : bool - OBV縺御ｸ頑・繝医Ξ繝ｳ繝峨↑繧欝rue
          OBV_Divergence  : bool - 萓｡譬ｼ縺御ｸ玖誠縺励※縺・ｋ縺ｮ縺ｫOBV縺御ｸ頑・・亥ｼｷ豌励ム繧､繝舌・繧ｸ繧ｧ繝ｳ繧ｹ・・
        """
        df = data.copy()
        close = df['Close']
        volume = df['Volume']

        direction = np.sign(close.diff().fillna(0))
        obv_series = (direction * volume).cumsum()
        df['OBV'] = obv_series

        df['OBV_SMA'] = obv_series.rolling(trend_days).mean()
        df['OBV_Trend_Up'] = obv_series.iloc[-1] > obv_series.iloc[-trend_days] if len(df) >= trend_days else False

        # 蠑ｷ豌励ム繧､繝舌・繧ｸ繧ｧ繝ｳ繧ｹ: 逶ｴ霑奏rend_days髢薙∽ｾ｡譬ｼ荳玖誠 & OBV荳頑・
        if len(df) >= trend_days:
            price_down = close.iloc[-1] < close.iloc[-trend_days]
            obv_up = obv_series.iloc[-1] > obv_series.iloc[-trend_days]
            df['OBV_Divergence'] = price_down and obv_up
        else:
            df['OBV_Divergence'] = False

        return df

    # 笏笏 蜃ｺ譚･鬮伜・譫・笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    @staticmethod
    def volume_analysis(data: pd.DataFrame, avg_period: int = 30) -> pd.DataFrame:
        """
        蜃ｺ譚･鬮倥・蜑肴律豈斐・蟷ｳ蝮・ｯ斐ｒ險育ｮ・

        霑ｽ蜉蛻・
          Volume_Ratio_1d   : 蜑肴律豈泌咲紫
          Volume_Ratio_Avg  : 30譌･蟷ｳ蝮・ｯ泌咲紫・・.5莉･荳・= 諤･蠅暦ｼ・
          Volume_Yen        : 螢ｲ雋ｷ莉｣驥托ｼ亥・・・
        """
        df = data.copy()
        vol = df['Volume']
        df['Volume_Yen'] = df['Close'] * vol
        df['Volume_Ratio_1d'] = vol / vol.shift(1).replace(0, np.nan)
        df['Volume_MA'] = vol.rolling(avg_period).mean()
        df['Volume_Ratio_Avg'] = vol / df['Volume_MA'].replace(0, np.nan)
        return df

    # 笏笏 VWAP・域律雜ｳ邨ょ､繝吶・繧ｹ霑台ｼｼ・俄楳笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    @staticmethod
    def vwap_daily_approx(data: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """
        譌･雜ｳ繝・・繧ｿ繧堤畑縺・◆VWAP霑台ｼｼ・・H+L+C)/3 ﾃ・Volume 縺ｮ邏ｯ遨肴ｯ費ｼ・

        窶ｻ 逵溘・VWAP縺ｯ譌･荳ｭ雜ｳ縺悟ｿ・ｦ√ゅ％繧後・繧ｻ繝・す繝ｧ繝ｳ蜀・ｿ台ｼｼ蛟､縲・
        霑ｽ蜉蛻・
          VWAP_Approx : 譛滄俣蜀・・VWAP霑台ｼｼ蛟､
          Above_VWAP  : 迴ｾ蝨ｨ蛟､縺祁WAP繧剃ｸ雁屓縺｣縺ｦ縺・ｋ縺・
        """
        df = data.copy()
        typical = (df['High'] + df['Low'] + df['Close']) / 3
        tp_vol = typical * df['Volume']
        df['VWAP_Approx'] = tp_vol.rolling(period).sum() / df['Volume'].rolling(period).sum()
        df['Above_VWAP'] = df['Close'] > df['VWAP_Approx']
        return df

    # 笏笏 遘ｻ蜍募ｹｳ蝮・& 荵夜屬邇・笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    @staticmethod
    def moving_averages(data: pd.DataFrame) -> pd.DataFrame:
        """
        MA25 / MA75 / MA200 縺ｨ荵夜屬邇・ｒ險育ｮ・

        霑ｽ蜉蛻・
          MA25 / MA75 / MA200
          MA25_Dev  : 25譌･荵夜屬邇・(%)   豁｣ = 荳頑婿荵夜屬
          MA75_Dev  : 75譌･荵夜屬邇・(%)
        """
        df = data.copy()
        close = df['Close']
        for period, col in [(MA_SHORT, 'MA25'), (MA_MID, 'MA75'), (MA_LONG, 'MA200')]:
            df[col] = close.rolling(period).mean()

        df['MA25_Dev'] = (close - df['MA25']) / df['MA25'].replace(0, np.nan) * 100
        df['MA75_Dev'] = (close - df['MA75']) / df['MA75'].replace(0, np.nan) * 100
        return df

    # 笏笏 荳逶ｮ蝮・｡｡陦ｨ 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    @staticmethod
    def ichimoku(data: pd.DataFrame) -> pd.DataFrame:
        """
        荳逶ｮ蝮・｡｡陦ｨ繧定ｨ育ｮ暦ｼ郁ｻ｢謠帷ｷ壹・蝓ｺ貅也ｷ壹・蜈郁｡後せ繝代Φ1/2繝ｻ驕・｡後せ繝代Φ・・

        霑ｽ蜉蛻・
          Ichi_Conv   : 霆｢謠帷ｷ・ (9譛滄俣鬮伜､+螳牙､)/2
          Ichi_Base   : 蝓ｺ貅也ｷ・ (26譛滄俣鬮伜､+螳牙､)/2
          Ichi_SpanA  : 蜈郁｡後せ繝代Φ1 (26譛滄俣蜈医↓謠冗判)
          Ichi_SpanB  : 蜈郁｡後せ繝代Φ2 (26譛滄俣蜈医↓謠冗判)
          Ichi_Lag    : 驕・｡後せ繝代Φ  (26譛滄俣蜑阪↓繧ｷ繝輔ヨ)
          Ichi_Cloud_Thick : 髮ｲ縺ｮ蜴壹＆・育ｵｶ蟇ｾ蛟､・・
          Ichi_Price_in_Cloud  : 萓｡譬ｼ縺碁峇縺ｮ荳ｭ
          Ichi_Price_above_Cloud : 萓｡譬ｼ縺碁峇縺ｮ荳・
          Ichi_Bullish : bool - 雋ｷ縺・だ繝ｼ繝ｳ蛻､螳・
        """
        df = data.copy()
        high = df['High']
        low  = df['Low']
        close = df['Close']

        # 霆｢謠帷ｷ壹・蝓ｺ貅也ｷ・
        def mid(h, l, p):
            return (h.rolling(p).max() + l.rolling(p).min()) / 2

        df['Ichi_Conv'] = mid(high, low, ICHIMOKU_CONV)
        df['Ichi_Base'] = mid(high, low, ICHIMOKU_BASE)

        # 蜈郁｡後せ繝代Φ・・6譌･蜈医す繝輔ヨ縺ｮ縺溘ａ縲∫樟蝨ｨ縺ｮ譛譁ｰ蛟､繧定ｨ育ｮ暦ｼ・
        df['Ichi_SpanA'] = ((df['Ichi_Conv'] + df['Ichi_Base']) / 2).shift(ICHIMOKU_LAG)
        df['Ichi_SpanB'] = mid(high, low, ICHIMOKU_SPAN2).shift(ICHIMOKU_LAG)

        # 驕・｡後せ繝代Φ・育樟蝨ｨ縺ｮ邨ょ､繧・6譌･蜑阪↓繧ｷ繝輔ヨ・・
        df['Ichi_Lag'] = close.shift(-ICHIMOKU_LAG)

        # 髮ｲ縺ｮ蛻・梵・亥・陦後せ繝代Φ縺ｯ繧ｷ繝輔ヨ蜑阪・迴ｾ蝨ｨ蛟､繧剃ｽｿ縺・ｼ・
        span_a_now = (df['Ichi_Conv'] + df['Ichi_Base']) / 2
        span_b_now = mid(high, low, ICHIMOKU_SPAN2)
        cloud_top    = np.maximum(span_a_now, span_b_now)
        cloud_bottom = np.minimum(span_a_now, span_b_now)

        df['Ichi_Cloud_Thick']       = (cloud_top - cloud_bottom) / close.replace(0, np.nan) * 100
        df['Ichi_Price_above_Cloud'] = close > cloud_top
        df['Ichi_Price_in_Cloud']    = (close >= cloud_bottom) & (close <= cloud_top)

        # 荳牙ｽｹ螂ｽ霆｢・育ｰ｡譏鍋沿・・
        #   1. 邨ょ､ > 髮ｲ縺ｮ荳・
        #   2. 霆｢謠帷ｷ・> 蝓ｺ貅也ｷ・
        #   3. 驕・｡後せ繝代Φ > 26譌･蜑阪・邨ょ､・・ close > close.shift(26)・・
        tenkan_above_kijun = df['Ichi_Conv'] > df['Ichi_Base']
        lag_above_price    = close > close.shift(ICHIMOKU_LAG)
        df['Ichi_Bullish'] = (
            df['Ichi_Price_above_Cloud'] &
            tenkan_above_kijun &
            lag_above_price
        )
        return df


class ScoringEngine:
    """
    蜷・欠讓吶ｒ 0縲・00 轤ｹ縺ｮ邱丞粋繧ｹ繧ｳ繧｢縺ｫ螟画鋤縺吶ｋ繧ｨ繝ｳ繧ｸ繝ｳ
    蜷・す繧ｰ繝翫Ν縺ｮON/OFF縺ｨ繧ｹ繧ｳ繧｢驟咲せ縺ｯ SCORE_WEIGHTS 縺ｧ邂｡逅・
    """

    @staticmethod
    def score(row: pd.Series, signals: Dict) -> Tuple[float, Dict]:
        """
        signals: {key: bool} 縺ｮ霎樊嶌縺九ｉ邱丞粋繧ｹ繧ｳ繧｢繧定ｨ育ｮ・
        Returns: (total_score, detail_dict)
        """
        detail = {}
        total = 0.0

        for key, weight in SCORE_WEIGHTS.items():
            if signals.get(key, False):
                total += weight
                detail[key] = weight
            else:
                detail[key] = 0

        return round(total, 1), detail


class HTMLReportGenerator:
    """
    HTML繝ｬ繝昴・繝育函謌舌け繝ｩ繧ｹ・医・繝ｼ繧ｷ繝・け繝ｻ繝励Ξ繝溘い繝蟇ｾ蠢懶ｼ・
    GitHub Pages逕ｨ縺ｮ髱咏噪HTML繧堤函謌・
    """

    def __init__(self, output_dir: str = "docs"):
        """
        Args:
            output_dir: 蜃ｺ蜉帙ョ繧｣繝ｬ繧ｯ繝医Μ・・itHub Pages縺ｮ繝ｫ繝ｼ繝茨ｼ・
        """
        self.output_dir = Path(output_dir)
        self.reports_dir = self.output_dir / "reports"
        self.premium_dir = self.output_dir / "premium"
        self.assets_dir = self.output_dir / "assets"

        # 繝・ぅ繝ｬ繧ｯ繝医Μ菴懈・
        for d in [self.reports_dir, self.premium_dir, self.assets_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def generate_basic_report(self, results: List[Dict], date: str,
                               sector_report: str = "") -> str:
        """
        繝吶・繧ｷ繝・け迚・TML繝ｬ繝昴・繝医ｒ逕滓・・亥ｽ捺律蜈ｨ莉ｶ・・

        Args:
            results: 繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ邨先棡
            date: 譌･莉俶枚蟄怜・・・YYY-MM-DD・・
            sector_report: 繧ｻ繧ｯ繧ｿ繝ｼ邨ｱ險・

        Returns:
            逕滓・縺励◆HTML繝輔ぃ繧､繝ｫ縺ｮ繝代せ・育嶌蟇ｾ・・
        """
        if not results:
            return ""

        date_str = date.replace("-", "")
        filename = f"{date_str}.html"
        filepath = self.reports_dir / filename

        # 繧ｽ繝ｼ繝亥庄閭ｽ縺ｪ繝・・繝悶ΝHTML
        html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ邨先棡 - {date}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{ font-size: 2em; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; font-size: 1.1em; }}
        .stats {{
            display: flex;
            justify-content: space-around;
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
        }}
        .stat-box {{
            text-align: center;
            padding: 15px;
        }}
        .stat-box .number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-box .label {{
            color: #6c757d;
            margin-top: 5px;
        }}
        .controls {{
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }}
        .controls input {{
            padding: 10px;
            border: 1px solid #ced4da;
            border-radius: 4px;
            width: 300px;
            font-size: 1em;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        thead {{
            background: #495057;
            color: white;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
            cursor: pointer;
            user-select: none;
        }}
        th:hover {{ background: #343a40; }}
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e9ecef;
        }}
        tr:hover {{ background: #f8f9fa; }}
        .score-high {{ color: #28a745; font-weight: bold; }}
        .score-mid {{ color: #ffc107; font-weight: bold; }}
        .score-low {{ color: #dc3545; font-weight: bold; }}
        .signal-yes {{ color: #28a745; }}
        .signal-no {{ color: #6c757d; }}
        .footer {{
            padding: 30px;
            text-align: center;
            background: #f8f9fa;
            color: #6c757d;
        }}
        .tag {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        .tag-safe {{ background: #d4edda; color: #155724; }}
        .tag-normal {{ background: #fff3cd; color: #856404; }}
        .tag-risky {{ background: #f8d7da; color: #721c24; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>投 譌･譛ｬ譬ｪ繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ邨先棡</h1>
            <p>套 {date} | 繝吶・繧ｷ繝・け繝励Λ繝ｳ</p>
        </div>

        <div class="stats">
            <div class="stat-box">
                <div class="number">{len(results)}</div>
                <div class="label">隧ｲ蠖馴釜譟・焚</div>
            </div>
            <div class="stat-box">
                <div class="number">{results[0]['total_score']:.0f}</div>
                <div class="label">譛鬮倥せ繧ｳ繧｢</div>
            </div>
            <div class="stat-box">
                <div class="number">{len(set(r['sector'] for r in results))}</div>
                <div class="label">繧ｻ繧ｯ繧ｿ繝ｼ謨ｰ</div>
            </div>
        </div>

        <div class="controls">
            <input type="text" id="search" placeholder="剥 驫俶氛蜷阪・繧ｳ繝ｼ繝峨〒讀懃ｴ｢..." onkeyup="filterTable()">
        </div>

        <div class="table-container">
        <table id="stockTable">
            <thead>
                <tr>
                    <th onclick="sortTable(0)">鬆・ｽ・/th>
                    <th onclick="sortTable(1)">繧ｳ繝ｼ繝・/th>
                    <th onclick="sortTable(2)">驫俶氛蜷・/th>
                    <th onclick="sortTable(3)">繧ｻ繧ｯ繧ｿ繝ｼ</th>
                    <th onclick="sortTable(4)">繧ｹ繧ｳ繧｢ 笆ｼ</th>
                    <th onclick="sortTable(5)">譬ｪ萓｡</th>
                    <th>繧ｷ繧ｰ繝翫Ν</th>
                    <th>繝ｪ繧ｹ繧ｯ</th>
                </tr>
            </thead>
            <tbody>
"""

        for i, r in enumerate(results, 1):
            score_class = ("score-high" if r['total_score'] >= 70
                          else "score-mid" if r['total_score'] >= 50
                          else "score-low")

            risk_class = ("tag-safe" if "螳牙ｮ・ in r['risk_tag']
                         else "tag-normal" if "讓呎ｺ・ in r['risk_tag']
                         else "tag-risky")

            signals = []
            if r['bottom_cross'] == '笨・: signals.append('蠎募､繧ｯ繝ｭ繧ｹ')
            if r['golden_cross'] == '笨・: signals.append('GC')
            if r['bb_reversal'] == '笨・: signals.append('BB蜿咲匱')
            if r['bb_breakout'] == '笨・: signals.append('BB繝悶Ξ繧､繧ｯ')
            if r['volume_surge'] == '笨・: signals.append('蜃ｺ譚･鬮俶･蠅・)
            if r['obv_trend_up'] == '笨・: signals.append('OBV竊・)
            if r['ichimoku_bullish'] != '窶・: signals.append('荳逶ｮ螂ｽ霆｢')

            signal_str = ", ".join(signals) if signals else "窶・

            html += f"""
                <tr>
                    <td>{i}</td>
                    <td><strong>{r['code']}</strong></td>
                    <td>{r['name']}</td>
                    <td><small>{r['sector']}</small></td>
                    <td class="{score_class}">{r['total_score']:.0f}</td>
                    <td>ﾂ･{r['price']:,.0f}</td>
                    <td><small>{signal_str}</small></td>
                    <td><span class="tag {risk_class}">{r['risk_tag']}</span></td>
                </tr>
"""

        html += """
            </tbody>
        </table>
        </div>  <!-- table-container -->

        <div class="footer">
            <p>東 縺薙・繝ｬ繝昴・繝医・蠖捺律髯舌ｊ譛牙柑縺ｧ縺吶らｿ梧律莉･髯阪・譛譁ｰ迚医ｒ縺皮｢ｺ隱阪￥縺縺輔＞縲・/p>
            <p style="margin-top: 10px;">
                <a href="../index.html" style="color: #667eea; text-decoration: none;">匠 繝医ャ繝励・繝ｼ繧ｸ縺ｸ</a> |
                <a href="#" style="color: #667eea; text-decoration: none;">荘 繝励Ξ繝溘い繝繝励Λ繝ｳ繧定ｦ九ｋ</a>
            </p>
        </div>
    </div>

    <script>
        function sortTable(col) {
            const table = document.getElementById("stockTable");
            const rows = Array.from(table.rows).slice(1);
            const isAsc = table.dataset.sortCol == col && table.dataset.sortDir == "asc";

            rows.sort((a, b) => {
                let aVal = a.cells[col].textContent.trim();
                let bVal = b.cells[col].textContent.trim();

                // 謨ｰ蛟､蛻励・蛻､螳・
                if (col === 4 || col === 5) {
                    aVal = parseFloat(aVal.replace(/[^0-9.-]/g, ''));
                    bVal = parseFloat(bVal.replace(/[^0-9.-]/g, ''));
                }

                return isAsc ? (aVal > bVal ? 1 : -1) : (aVal < bVal ? 1 : -1);
            });

            rows.forEach(row => table.tBodies[0].appendChild(row));
            table.dataset.sortCol = col;
            table.dataset.sortDir = isAsc ? "desc" : "asc";
        }

        function filterTable() {
            const input = document.getElementById("search").value.toUpperCase();
            const table = document.getElementById("stockTable");
            const rows = table.getElementsByTagName("tr");

            for (let i = 1; i < rows.length; i++) {
                const code = rows[i].cells[1].textContent;
                const name = rows[i].cells[2].textContent;
                rows[i].style.display = (code + name).toUpperCase().includes(input) ? "" : "none";
            }
        }
    </script>
</body>
</html>
"""

        filepath.write_text(html, encoding='utf-8')
        print(f"笨・HTML繝ｬ繝昴・繝育函謌・ {filepath}")
        return f"reports/{filename}"

    def generate_index_page(self, latest_report_path: str = "",
                             total_stocks: int = 0) -> str:
        """
        繝医ャ繝励・繝ｼ繧ｸ・医・繝ｩ繝ｳ隱ｬ譏弱・譛譁ｰ繝ｬ繝昴・繝医Μ繝ｳ繧ｯ・峨ｒ逕滓・

        Returns:
            逕滓・縺励◆index.html縺ｮ繝代せ
        """
        filepath = self.output_dir / "index.html"

        html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>譌･譛ｬ譬ｪ繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ - Multi-Plan Service</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 10px;
            color: #333;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .header h1 {{ font-size: 1.5em; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; font-size: 1em; }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 10px;
            padding: 15px;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
        }}
        .stat-box {{
            text-align: center;
            padding: 10px;
        }}
        .stat-box .number {{
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-box .label {{
            color: #6c757d;
            margin-top: 5px;
            font-size: 0.85em;
        }}
        
        .controls {{
            padding: 15px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }}
        .controls input {{
            padding: 10px;
            border: 1px solid #ced4da;
            border-radius: 4px;
            width: 100%;
            font-size: 1em;
        }}
        
        /* 繝・・繝悶Ν - 繝｢繝舌う繝ｫ譛驕ｩ蛹・*/
        .table-container {{
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            min-width: 600px;
        }}
        thead {{
            background: #495057;
            color: white;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        th {{
            padding: 12px 8px;
            text-align: left;
            font-weight: 600;
            cursor: pointer;
            user-select: none;
            font-size: 0.9em;
        }}
        th:hover {{ background: #343a40; }}
        td {{
            padding: 10px 8px;
            border-bottom: 1px solid #e9ecef;
            font-size: 0.85em;
        }}
        tr:hover {{ background: #f8f9fa; }}
        
        .score-high {{ color: #28a745; font-weight: bold; }}
        .score-mid {{ color: #ffc107; font-weight: bold; }}
        .score-low {{ color: #dc3545; font-weight: bold; }}
        .signal-yes {{ color: #28a745; }}
        .signal-no {{ color: #6c757d; }}
        
        .tag {{
            display: inline-block;
            padding: 3px 6px;
            border-radius: 4px;
            font-size: 0.75em;
            font-weight: 600;
            white-space: nowrap;
        }}
        .tag-safe {{ background: #d4edda; color: #155724; }}
        .tag-normal {{ background: #fff3cd; color: #856404; }}
        .tag-risky {{ background: #f8d7da; color: #721c24; }}
        
        .footer {{
            padding: 20px;
            text-align: center;
            background: #f8f9fa;
            color: #6c757d;
            font-size: 0.9em;
        }}
        .footer a {{
            color: #667eea;
            text-decoration: none;
            margin: 0 10px;
        }}
        
        /* 繧ｹ繝槭・蟇ｾ蠢・*/
        @media (max-width: 768px) {{
            body {{ padding: 5px; }}
            .container {{ border-radius: 8px; }}
            .header {{ padding: 15px; }}
            .header h1 {{ font-size: 1.3em; }}
            .header p {{ font-size: 0.9em; }}
            
            .stats {{
                grid-template-columns: repeat(3, 1fr);
                gap: 8px;
                padding: 10px;
            }}
            .stat-box {{ padding: 8px; }}
            .stat-box .number {{ font-size: 1.3em; }}
            .stat-box .label {{ font-size: 0.75em; }}
            
            .controls {{ padding: 10px; }}
            .controls input {{ font-size: 16px; /* iOS zoom髦ｲ豁｢ */ }}
            
            th {{ padding: 10px 6px; font-size: 0.8em; }}
            td {{ padding: 8px 6px; font-size: 0.8em; }}
            
            .footer {{ padding: 15px 10px; font-size: 0.85em; }}
            .footer a {{ display: block; margin: 8px 0; }}
        }}
        
        /* 讌ｵ蟆上せ繝槭・蟇ｾ蠢・*/
        @media (max-width: 480px) {{
            .header h1 {{ font-size: 1.1em; }}
            .stats {{ grid-template-columns: repeat(3, 1fr); }}
            .stat-box .number {{ font-size: 1.2em; }}
            th, td {{ font-size: 0.75em; padding: 8px 4px; }}
            table {{ min-width: 500px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>投 譌･譛ｬ譬ｪ繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ</h1>
            <p>yfinance繝吶・繧ｹ縺ｮ繝・け繝九き繝ｫ蛻・梵縺ｧ縲∵ｯ取律繧ｷ繧ｰ繝翫Ν驫俶氛繧偵♀螻翫￠</p>
        </div>

        <div class="plans">
            <div class="plan">
                <h2>・ 辟｡蜆溽沿</h2>
                <div class="price">FREE</div>
                <ul>
                    <li>蜴ｳ驕ｸ3驫俶氛繧呈ｯ取律騾夂衍</li>
                    <li>荳ｭ菴阪せ繧ｳ繧｢ﾃ怜､壽ｧ俶ｧ謌ｦ逡･</li>
                    <li>Slack/Discord蟇ｾ蠢・/li>
                </ul>
                <a href="#" class="btn">辟｡譁咏匳骭ｲ</a>
            </div>

            <div class="plan">
                <h2>直 繝吶・繧ｷ繝・け</h2>
                <div class="price">ﾂ･980<small>/譛・/small></div>
                <ul>
                    <li>蜈ｨ驫俶氛HTML繝ｬ繝昴・繝・/li>
                    <li>蠖捺律蛻・・縺ｿ髢ｲ隕ｧ蜿ｯ閭ｽ</li>
                    <li>繧ｽ繝ｼ繝医・讀懃ｴ｢讖溯・</li>
                    <li>蜈ｨ謖・ｨ吶せ繧ｳ繧｢陦ｨ遉ｺ</li>
                </ul>
                <a href="{latest_report_path}" class="btn">譛譁ｰ繝ｬ繝昴・繝医ｒ隕九ｋ</a>
            </div>

            <div class="plan">
                <h2>荘 繝励Ξ繝溘い繝</h2>
                <div class="price">ﾂ･1,980<small>/譛・/small></div>
                <ul>
                    <li>30譌･蛻・い繝ｼ繧ｫ繧､繝・/li>
                    <li>蜷・釜譟・メ繝｣繝ｼ繝郁｡ｨ遉ｺ</li>
                    <li>繧ｷ繧ｰ繝翫Ν逋ｺ逕溷ｱ･豁ｴ</li>
                    <li>蜍晉紫邨ｱ險医げ繝ｩ繝・/li>
                </ul>
                <a href="#" class="btn">繝励Ξ繝溘い繝逋ｻ骭ｲ</a>
            </div>
        </div>

        <div class="latest">
            <h3>塘 譛譁ｰ繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ邨先棡</h3>
            <p style="color: #6c757d; margin-bottom: 20px;">
                譛ｬ譌･ {total_stocks}驫俶氛縺梧擅莉ｶ縺ｫ蜷郁・縺励∪縺励◆
            </p>
            <a href="{latest_report_path}" class="btn">繝ｬ繝昴・繝医ｒ隕九ｋ</a>
        </div>
    </div>
</body>
</html>
"""

        filepath.write_text(html, encoding='utf-8')
        print(f"笨・繝医ャ繝励・繝ｼ繧ｸ逕滓・: {filepath}")
        return "index.html"


class AdvancedStockScreener:
    """
    鬮伜ｺｦ縺ｪ譌･譛ｬ譬ｪ繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ繧ｯ繝ｩ繧ｹ v2.0
    笏 yfinance縺ｮ縺ｿ縺ｧ蜍穂ｽ懊☆繧句・謖・ｨ吶ｒ邨ｱ蜷・
    """

    def __init__(self,
                 min_volume: int = 1_000_000,
                 enable_backtest: bool = True,
                 min_score: float = 30.0):
        """
        Args:
            min_volume   : 譛菴・0譌･蟷ｳ蝮・｣ｲ雋ｷ莉｣驥托ｼ亥・・・
            enable_backtest : 繝舌ャ繧ｯ繝・せ繝域ｩ溯・繧呈怏蜉ｹ蛹・
            min_score    : 繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ騾夐℃縺ｮ譛菴弱せ繧ｳ繧｢・・縲・00・・
        """
        self.min_volume    = min_volume
        self.enable_backtest = enable_backtest
        self.min_score     = min_score
        self.results       = []
        self.sector_stats  = defaultdict(int)
        self.ti            = TechnicalIndicators()
        self.scorer        = ScoringEngine()

    def select_free_tier_stocks(self, results: List[Dict], count: int = 3) -> List[Dict]:
        """
        辟｡譁咏沿逕ｨ・壻ｸｭ菴阪せ繧ｳ繧｢蟶ｯ縺九ｉ螟壽ｧ俶ｧ繧呈戟縺｣縺ｦ驕ｸ謚・

        謌ｦ逡･:
          1. 繧ｹ繧ｳ繧｢50縲・5縺ｮ荳ｭ菴榊ｸｯ繧呈歓蜃ｺ
          2. 豬∝虚諤ｧ・亥ｮ牙ｿ・─・峨〒繧ｽ繝ｼ繝・
          3. 繧ｻ繧ｯ繧ｿ繝ｼ驥崎､・ｒ驕ｿ縺代※驕ｸ謚・
          4. 縲後→縺｣縺ｦ縺翫″縺ｯ蜃ｺ縺輔↑縺・阪′縲∝ｮ牙ｮ壽─縺ｯ蜃ｺ縺・

        Args:
            results: 蜈ｨ繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ邨先棡・医せ繧ｳ繧｢鬆・た繝ｼ繝域ｸ医∩・・
            count: 驕ｸ謚懈焚

        Returns:
            驕ｸ謚懊＆繧後◆驫俶氛繝ｪ繧ｹ繝・
        """
        # 荳ｭ菴阪せ繧ｳ繧｢蟶ｯ繧呈歓蜃ｺ・・0縲・5轤ｹ・・
        mid_tier = [r for r in results if 50 <= r['total_score'] < 75]

        if not mid_tier:
            # 荳ｭ菴榊ｸｯ縺後↑縺・ｴ蜷医・蜈ｨ菴薙°繧蛾∈縺ｶ
            mid_tier = results

        # 豬∝虚諤ｧ縺ｧ繧ｽ繝ｼ繝茨ｼ井ｿ｡鬆ｼ諢溘・螳牙ｿ・─繧貞━蜈茨ｼ・
        mid_tier.sort(key=lambda x: x['avg_volume_30d'], reverse=True)

        # 繧ｻ繧ｯ繧ｿ繝ｼ驥崎､・ｒ驕ｿ縺代※驕ｸ謚・
        selected = []
        used_sectors = set()

        for stock in mid_tier:
            if stock['sector'] not in used_sectors:
                selected.append(stock)
                used_sectors.add(stock['sector'])
                if len(selected) == count:
                    break

        # 莉ｶ謨ｰ縺ｫ貅縺溘↑縺・ｴ蜷医・驥崎､・ｒ險ｱ螳ｹ縺励※霑ｽ蜉
        if len(selected) < count:
            for stock in mid_tier:
                if stock not in selected:
                    selected.append(stock)
                    if len(selected) == count:
                        break

        return selected

    # 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    #  驫俶氛繝ｪ繧ｹ繝亥叙蠕暦ｼ域里蟄倥Ο繧ｸ繝・け邯ｭ謖・ｼ・
    # 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    def get_jpx_stock_list(self) -> pd.DataFrame:
        """譚ｱ險ｼ繧ｳ繝ｼ繝臥ｷ丞ｽ薙◆繧頑婿蠑擾ｼ域里蟄倥Ο繧ｸ繝・け邯ｭ謖・ｼ・""
        print("踏 譚ｱ險ｼ驫俶氛繝ｪ繧ｹ繝医ｒ逕滓・荳ｭ・医さ繝ｼ繝臥ｷ丞ｽ薙◆繧頑婿蠑擾ｼ・..")
        code_ranges = (
            list(range(1300, 1500)) +
            list(range(1700, 2000)) +
            list(range(2000, 9999))
        )
        stocks = [{'code': str(c).zfill(4), 'name': str(c), 'sector': '荳肴・'}
                  for c in code_ranges]
        df = pd.DataFrame(stocks)
        print(f"笨・{len(df)}莉ｶ縺ｮ繧ｳ繝ｼ繝峨ｒ逕滓・縺励∪縺励◆")
        return df

    def _get_sample_stocks(self) -> pd.DataFrame:
        """繧ｵ繝ｳ繝励Ν驫俶氛繝ｪ繧ｹ繝茨ｼ磯幕逋ｺ繝ｻ繝・せ繝育畑・・""
        return pd.DataFrame({
            'code': ['7203','8306','9984','6758','8001',
                     '9432','6861','7974','4063','4502'],
            'name': ['繝医Κ繧ｿ','荳芽廠UFJ','繧ｽ繝輔ヨ繝舌Φ繧ｯG','繧ｽ繝九・G','莨願陸蠢',
                     'NTT','繧ｭ繝ｼ繧ｨ繝ｳ繧ｹ','莉ｻ螟ｩ蝣・,'菫｡雜雁喧蟄ｦ','豁ｦ逕ｰ阮ｬ蜩・],
            'sector': ['霈ｸ騾∫畑讖溷勣','驫陦・,'諠・ｱ繝ｻ騾壻ｿ｡','髮ｻ豌玲ｩ溷勣','蜊ｸ螢ｲ',
                       '諠・ｱ繝ｻ騾壻ｿ｡','髮ｻ豌玲ｩ溷勣','縺昴・莉冶｣ｽ蜩・,'蛹門ｭｦ','蛹ｻ阮ｬ蜩・]
        })

    # 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    #  譌｢蟄倥Γ繧ｽ繝・ラ・亥ｾ梧婿莠呈鋤縺ｮ縺溘ａ邯ｭ謖・ｼ・
    # 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    def calculate_ma(self, prices: pd.Series, period: int) -> pd.Series:
        """遘ｻ蜍募ｹｳ蝮・ｷ壹ｒ險育ｮ暦ｼ亥ｾ梧婿莠呈鋤・・""
        return prices.rolling(window=period).mean()

    def is_ma_trending_up(self, ma: pd.Series, lookback: int = 5,
                          min_slope: float = 0.0001) -> bool:
        """MA荳頑・繝医Ξ繝ｳ繝牙愛螳夲ｼ亥ｾ梧婿莠呈鋤・・""
        if len(ma.dropna()) < lookback:
            return False
        recent_ma = ma.dropna().iloc[-lookback:].values
        normalized = recent_ma / recent_ma[0]
        slope = np.polyfit(np.arange(lookback), normalized, 1)[0]
        return slope > min_slope

    # 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    #  繝舌ャ繧ｯ繝・せ繝茨ｼ域里蟄倥Ο繧ｸ繝・け邯ｭ謖√・諡｡蠑ｵ・・
    # 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    def detect_signal_dates(self, data: pd.DataFrame) -> List[str]:
        """驕主悉繧ｷ繧ｰ繝翫Ν逋ｺ逕滓律繧呈､懷・・医ヰ繝・け繝・せ繝育畑・・""
        signal_dates = []
        for i in range(MA_LONG, len(data)):
            current = data.iloc[i]
            bottom_cross = (current['Low'] <= current['MA200'] < current['Close'])
            golden_cross = False
            if i > 0:
                prev = data.iloc[i - 1]
                golden_cross = (prev['MA50'] < prev['MA100'] and
                                current['MA50'] >= current['MA100'])
            if bottom_cross or golden_cross:
                signal_dates.append(current.name.strftime('%Y-%m-%d'))
        return signal_dates

    def calculate_win_rate(self, data: pd.DataFrame, signal_dates: List[str],
                           forward_days: int = 5) -> Tuple[float, int, int]:
        """繧ｷ繧ｰ繝翫Ν蠕悟享邇・ｒ險育ｮ暦ｼ亥ｾ梧婿莠呈鋤・・""
        if not signal_dates:
            return 0.0, 0, 0
        wins, total = 0, 0
        for sd in signal_dates:
            try:
                idx = data.index.get_loc(sd)
                if idx + forward_days < len(data):
                    if data['Close'].iloc[idx + forward_days] > data['Close'].iloc[idx]:
                        wins += 1
                    total += 1
            except (KeyError, ValueError):
                continue
        return (wins / total * 100) if total > 0 else 0.0, wins, total

    def calculate_volatility(self, data: pd.DataFrame, window: int = 20) -> float:
        """繝懊Λ繝・ぅ繝ｪ繝・ぅ・亥ｹｴ邇・ｼ峨ｒ險育ｮ・""
        returns = data['Close'].pct_change()
        return returns.tail(window).std() * np.sqrt(252) * 100

    # 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    #  菫｡逕ｨ蛟咲紫繧ｹ繧ｳ繧｢・・icker.info 縺九ｉ蜿門ｾ暦ｼ・
    # 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    def get_short_score(self, info: Dict) -> Tuple[float, str]:
        """
        菫｡逕ｨ蛟咲紫繝ｻ繧ｷ繝ｧ繝ｼ繝域ｯ皮紫縺九ｉ繧ｹ繧ｳ繧｢繧定ｨ育ｮ・

        - short_ratio     : 雋ｸ譬ｪ谿矩ｫ・/ 1譌･蟷ｳ蝮・・譚･鬮假ｼ郁ｿ疲ｸ医↓縺九°繧区律謨ｰ・・
          竊・鬮倥＞縺ｻ縺ｩ螢ｲ繧頑婿縺ｮ縲後＠縺薙ｊ縲阪′螟ｧ縺阪＞・医す繝ｧ繝ｼ繝医せ繧ｯ繧､繝ｼ繧ｺ蛟呵｣懶ｼ・
        - short_float_pct : Float譬ｪ謨ｰ縺ｫ蟇ｾ縺吶ｋ繧ｷ繝ｧ繝ｼ繝域ｯ皮紫(%)

        Returns:
            (score 0縲・.0, 隱ｬ譏弱Λ繝吶Ν)
        """
        short_ratio = info.get('shortRatio')         # 萓・ 3.5 譌･
        short_float = info.get('shortPercentOfFloat')  # 萓・ 0.12 = 12%

        label_parts = []
        score = 0.0

        if short_ratio is not None:
            label_parts.append(f"ShortRatio:{short_ratio:.1f}譌･")
            # 5譌･莉･荳・竊・縺励％繧雁､ｧ 竊・繧ｹ繧ｯ繧､繝ｼ繧ｺ譛溷ｾ・
            if short_ratio >= 10:
                score += 1.0
            elif short_ratio >= 5:
                score += 0.6
            elif short_ratio >= 2:
                score += 0.3

        if short_float is not None:
            pct = short_float * 100 if short_float < 1 else short_float
            label_parts.append(f"ShortFloat:{pct:.1f}%")
            # 20%莉･荳・竊・鬮倥す繝ｧ繝ｼ繝・竊・繧ｹ繧ｯ繧､繝ｼ繧ｺ蛟呵｣・
            if pct >= 20:
                score = min(score + 1.0, 1.0)
            elif pct >= 10:
                score = min(score + 0.5, 1.0)

        if not label_parts:
            return 0.0, "N/A"

        return min(score, 1.0), " / ".join(label_parts)

    # 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    #  繝｡繧､繝ｳ繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ
    # 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    def screen_stock(self, code: str, name: str, sector: str = "荳肴・") -> Optional[Dict]:
        """蛟句挨驫俶氛繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ・・2.0 蜈ｨ謖・ｨ咏ｵｱ蜷育沿・・""
        ticker_symbol = f"{code}.T"

        try:
            ticker = yf.Ticker(ticker_symbol)
            # 繝舌ャ繧ｯ繝・せ繝・+ 荳逶ｮ蝮・｡｡陦ｨ縺ｫ蜊∝・縺ｪ繝・・繧ｿ遒ｺ菫晢ｼ域怙菴・蟷ｴ・・
            data = ticker.history(period="2y")

            if data.empty or len(data) < MA_LONG:
                return None

            # 笏笏 驫俶氛蜷阪・繧ｻ繧ｯ繧ｿ繝ｼ陬懷ｮ・笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
            info = {}
            if name == code:
                try:
                    info = ticker.info
                    name   = info.get('longName') or info.get('shortName') or code
                    sector = info.get('sector') or info.get('industry') or '荳肴・'
                except Exception:
                    pass
            else:
                try:
                    info = ticker.info
                except Exception:
                    pass

            # 笏笏 繝・け繝九き繝ｫ謖・ｨ吶ｒ荳諡ｬ險育ｮ・笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
            data = TechnicalIndicators.bollinger_bands(data)
            data = TechnicalIndicators.obv(data)
            data = TechnicalIndicators.volume_analysis(data)
            data = TechnicalIndicators.vwap_daily_approx(data)
            data = TechnicalIndicators.moving_averages(data)
            data = TechnicalIndicators.ichimoku(data)

            # MA50/100 縺ｯ譌｢蟄倥ヰ繝・け繝・せ繝育畑縺ｫ霑ｽ蜉
            data['MA50']  = data['Close'].rolling(50).mean()
            data['MA100'] = data['Close'].rolling(100).mean()

            # 笏笏 豬∝虚諤ｧ繝√ぉ繝・け 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
            avg_volume_30d = data['Volume_Yen'].tail(30).mean()
            if avg_volume_30d < self.min_volume:
                return None

            latest = data.iloc[-1]
            prev   = data.iloc[-2] if len(data) >= 2 else latest

            # 笏笏 譌｢蟄倥す繧ｰ繝翫Ν 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
            ma200_trending = self.is_ma_trending_up(data['MA200'])
            bottom_cross   = bool(latest['Low'] <= latest['MA200'] < latest['Close'])
            golden_cross   = bool(prev['MA50'] < prev['MA100'] and
                                  latest['MA50'] >= latest['MA100'])

            # 笏笏 繝懊Μ繝ｳ繧ｸ繝｣繝ｼ繝舌Φ繝峨す繧ｰ繝翫Ν 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
            pct_b   = latest.get('BB_Pct_B', np.nan)
            bb_width = latest.get('BB_Width', np.nan)
            # 蜿咲匱蛟呵｣・ %b <= 0.2 (荳矩剞莉倩ｿ・ 縺九▽繝舌Φ繝牙ｹ・′蜿守ｸｮ縺励※縺・↑縺・
            bb_reversal    = (not np.isnan(pct_b)) and (pct_b <= 0.2)
            # 繝悶Ξ繧､繧ｯ繧｢繧ｦ繝亥呵｣・ %b >= 1.0 (荳企剞遯∫ｴ) 縺九▽蜃ｺ譚･鬮俶･蠅・
            bb_breakout    = (not np.isnan(pct_b)) and (pct_b >= 1.0)
            bb_signal      = bb_reversal or bb_breakout

            # %b 縺ｮ隱ｬ譏弱Λ繝吶Ν
            if np.isnan(pct_b):
                bb_label = "N/A"
            elif pct_b <= 0.0:
                bb_label = f"筮・ｸ矩剞蜑ｲ繧・{pct_b:.2f})"
            elif pct_b <= 0.2:
                bb_label = f"桃荳矩剞莉倩ｿ・{pct_b:.2f})"
            elif pct_b >= 1.0:
                bb_label = f"噫荳企剞遯∫ｴ({pct_b:.2f})"
            elif pct_b >= 0.8:
                bb_label = f"嶋荳企剞莉倩ｿ・{pct_b:.2f})"
            else:
                bb_label = f"荳ｭ髢・{pct_b:.2f})"

            # 笏笏 蜃ｺ譚･鬮倥す繧ｰ繝翫Ν 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
            vol_ratio_avg  = latest.get('Volume_Ratio_Avg', 1.0)
            vol_ratio_1d   = latest.get('Volume_Ratio_1d', 1.0)
            volume_surge   = bool(vol_ratio_avg >= 1.5)  # 30譌･蟷ｳ蝮・・1.5蛟堺ｻ･荳・

            # 笏笏 OBV繧ｷ繧ｰ繝翫Ν 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
            obv_trend_up    = bool(latest.get('OBV_Trend_Up', False))
            obv_divergence  = bool(latest.get('OBV_Divergence', False))
            obv_signal      = obv_trend_up  # 繧ｹ繧ｳ繧｢縺ｫ縺ｯ繝医Ξ繝ｳ繝峨ｒ菴ｿ逕ｨ

            # 笏笏 荳逶ｮ蝮・｡｡陦ｨ繧ｷ繧ｰ繝翫Ν 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
            ichimoku_bullish     = bool(latest.get('Ichi_Bullish', False))
            above_cloud          = bool(latest.get('Ichi_Price_above_Cloud', False))
            in_cloud             = bool(latest.get('Ichi_Price_in_Cloud', False))
            cloud_thick          = latest.get('Ichi_Cloud_Thick', 0.0)

            if ichimoku_bullish:
                ichi_label = "泙荳牙ｽｹ螂ｽ霆｢"
            elif above_cloud:
                ichi_label = "鳩髮ｲ縺ｮ荳・
            elif in_cloud:
                ichi_label = "泯髮ｲ縺ｮ荳ｭ"
            else:
                ichi_label = "閥髮ｲ縺ｮ荳・

            # 笏笏 遘ｻ蜍募ｹｳ蝮・ｹ夜屬邇・笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
            ma25_dev = latest.get('MA25_Dev', np.nan)
            ma75_dev = latest.get('MA75_Dev', np.nan)

            # 笏笏 VWAP 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
            above_vwap = bool(latest.get('Above_VWAP', False))

            # 笏笏 菫｡逕ｨ蛟咲紫・・icker.info・俄楳笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
            short_score_raw, short_label = self.get_short_score(info)
            short_squeeze = short_score_raw >= 0.5  # 50%莉･荳翫〒繧ｷ繧ｰ繝翫Ν謇ｱ縺・

            # 笏笏 邱丞粋繧ｹ繧ｳ繧｢險育ｮ・笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
            signals = {
                'ma_trend'      : ma200_trending,
                'golden_cross'  : golden_cross,
                'bottom_cross'  : bottom_cross,
                'bb_signal'     : bb_signal,
                'obv_trend'     : obv_signal,
                'ichimoku'      : ichimoku_bullish or above_cloud,
                'volume_surge'  : volume_surge,
                'short_squeeze' : short_squeeze,
            }
            total_score, score_detail = self.scorer.score(latest, signals)

            # 笏笏 繧ｹ繧ｳ繧｢繝輔ぅ繝ｫ繧ｿ 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
            if total_score < self.min_score:
                return None

            # 笏笏 繝舌ャ繧ｯ繝・せ繝茨ｼ域里蟄倥Ο繧ｸ繝・け邯ｭ謖・ｼ俄楳笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
            win_rate, backtest_sample = 0.0, 0
            if self.enable_backtest:
                signal_dates = self.detect_signal_dates(data)
                win_rate, _, total_bt = self.calculate_win_rate(data, signal_dates)
                backtest_sample = total_bt

            # 笏笏 繝懊Λ繝・ぅ繝ｪ繝・ぅ & 繝ｪ繧ｹ繧ｯ繧ｿ繧ｰ 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
            volatility = self.calculate_volatility(data)
            if avg_volume_30d >= 100_000_000:
                risk_tag = "泙螳牙ｮ・
            elif avg_volume_30d >= 10_000_000:
                risk_tag = "泯讓呎ｺ・
            else:
                risk_tag = "閥蜀帝匱"

            # 笏笏 繧ｻ繧ｯ繧ｿ繝ｼ邨ｱ險域峩譁ｰ 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
            self.sector_stats[sector] += 1

            return {
                # 笏笏 蝓ｺ譛ｬ諠・ｱ 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
                'code'              : code,
                'name'              : name,
                'sector'            : sector,
                'price'             : latest['Close'],
                'date'              : latest.name.strftime('%Y-%m-%d'),

                # 笏笏 邱丞粋繧ｹ繧ｳ繧｢ 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
                'total_score'       : total_score,
                'score_detail'      : score_detail,

                # 笏笏 譌｢蟄倥す繧ｰ繝翫Ν 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
                'ma200_trend'       : '荳頑・' if ma200_trending else '讓ｪ縺ｰ縺・荳玖誠',
                'bottom_cross'      : '笨・ if bottom_cross else '窶・,
                'golden_cross'      : '笨・ if golden_cross else '窶・,

                # 笏笏 繝懊Μ繝ｳ繧ｸ繝｣繝ｼ繝舌Φ繝・笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
                'bb_pct_b'          : round(pct_b, 3) if not np.isnan(pct_b) else None,
                'bb_width'          : round(bb_width, 4) if not np.isnan(bb_width) else None,
                'bb_label'          : bb_label,
                'bb_reversal'       : '笨・ if bb_reversal else '窶・,
                'bb_breakout'       : '笨・ if bb_breakout else '窶・,

                # 笏笏 蜃ｺ譚･鬮・笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
                'avg_volume_30d'    : avg_volume_30d,
                'volume_ratio_1d'   : round(vol_ratio_1d, 2),
                'volume_ratio_avg'  : round(vol_ratio_avg, 2),
                'volume_surge'      : '笨・ if volume_surge else '窶・,

                # 笏笏 OBV 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
                'obv_trend_up'      : '笨・ if obv_trend_up else '窶・,
                'obv_divergence'    : '笨・ｼｷ豌優' if obv_divergence else '窶・,

                # 笏笏 VWAP 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
                'above_vwap'        : '笨・ if above_vwap else '窶・,
                'vwap_approx'       : round(latest.get('VWAP_Approx', 0), 1),

                # 笏笏 遘ｻ蜍募ｹｳ蝮・ｹ夜屬邇・笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
                'ma25_dev'          : round(ma25_dev, 2) if not np.isnan(ma25_dev) else None,
                'ma75_dev'          : round(ma75_dev, 2) if not np.isnan(ma75_dev) else None,

                # 笏笏 荳逶ｮ蝮・｡｡陦ｨ 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
                'ichimoku_label'    : ichi_label,
                'ichimoku_bullish'  : '笨・ｸ牙ｽｹ螂ｽ霆｢' if ichimoku_bullish else '窶・,
                'cloud_thick_pct'   : round(cloud_thick, 2) if not np.isnan(cloud_thick) else None,

                # 笏笏 菫｡逕ｨ蛟咲紫・・nfo・俄楳笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
                'short_info'        : short_label,
                'short_squeeze'     : '笨・ if short_squeeze else '窶・,

                # 笏笏 繝ｪ繧ｹ繧ｯ繝ｻ繝舌ャ繧ｯ繝・せ繝・笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
                'volatility'        : volatility,
                'risk_tag'          : risk_tag,
                'win_rate'          : win_rate,
                'backtest_sample'   : backtest_sample,
            }

        except Exception:
            return None

    # 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    #  蜈ｨ驫俶氛繧ｹ繧ｭ繝｣繝ｳ
    # 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    def scan_all_stocks(self, max_stocks: Optional[int] = None,
                        use_sample: bool = False) -> List[Dict]:
        """蜈ｨ驫俶氛繧ｹ繧ｭ繝｣繝ｳ"""
        print("投 驫俶氛繝ｪ繧ｹ繝医ｒ蜿門ｾ嶺ｸｭ...")
        stocks_df = self._get_sample_stocks() if use_sample else self.get_jpx_stock_list()

        if max_stocks:
            stocks_df = stocks_df.head(max_stocks)

        total = len(stocks_df)
        print(f"剥 {total}驫俶氛縺ｮ繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ繧帝幕蟋具ｼ域怙菴弱せ繧ｳ繧｢: {self.min_score}轤ｹ・噂n")

        results = []
        for idx, row in stocks_df.iterrows():
            code   = row['code']
            name   = row['name']
            sector = row.get('sector', '荳肴・')

            if (idx + 1) % 50 == 0:
                print(f"騾ｲ謐・ {idx + 1}/{total} ({len(results)}驫俶氛蜷郁・)")

            result = self.screen_stock(code, name, sector)
            if result:
                results.append(result)
                print(f"  笨・{code} {result['name']} "
                      f"[{sector}] 繧ｹ繧ｳ繧｢:{result['total_score']}轤ｹ")

            time.sleep(0.5)

        print(f"\n笨・繧ｹ繧ｭ繝｣繝ｳ螳御ｺ・ {len(results)}驫俶氛縺梧擅莉ｶ縺ｫ蜷郁・")

        # 邱丞粋繧ｹ繧ｳ繧｢ 竊・蜍晉紫 縺ｮ鬆・〒繧ｽ繝ｼ繝・
        results.sort(key=lambda x: (x['total_score'], x['win_rate']), reverse=True)
        return results

    # 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    #  繧ｻ繧ｯ繧ｿ繝ｼ繝ｬ繝昴・繝茨ｼ域里蟄倡ｶｭ謖・ｼ・
    # 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    def generate_sector_report(self) -> str:
        """繧ｻ繧ｯ繧ｿ繝ｼ蛻･繝ｬ繝昴・繝育函謌・""
        if not self.sector_stats:
            return ""
        report = "\n投 繧ｻ繧ｯ繧ｿ繝ｼ蛻･蜀・ｨｳ:\n"
        for sector, count in sorted(self.sector_stats.items(),
                                     key=lambda x: x[1], reverse=True)[:5]:
            report += f"  窶｢ {sector}: {count}驫俶氛\n"
        return report


class AdvancedNotifier:
    """
    諡｡蠑ｵ騾夂衍繧ｯ繝ｩ繧ｹ v3.0・・繝励Λ繝ｳ蟇ｾ蠢懶ｼ・
    笏 繝励Λ繝ｳ縺ｫ蠢懊§縺ｦ騾夂衍蜀・ｮｹ繧貞・繧頑崛縺・
    """

    def __init__(self, service: str = "slack", plan_mode: str = "free_beta"):
        """
        Args:
            service: 騾夂衍繧ｵ繝ｼ繝薙せ・・lack / discord・・
            plan_mode: 繝励Λ繝ｳ繝｢繝ｼ繝・
                - "free_beta": 證ｫ螳夂┌蜆溽沿・・莉ｶ+HTML繝ｪ繝ｳ繧ｯ・・
                - "free": 豁｣蠑冗┌蜆溽沿・・莉ｶ縺ｮ縺ｿ・・
                - "basic": 繝吶・繧ｷ繝・け・・TML繝ｪ繝ｳ繧ｯ驥崎ｦ厄ｼ・
                - "premium": 繝励Ξ繝溘い繝・・TML繝ｪ繝ｳ繧ｯ驥崎ｦ厄ｼ・
        """
        self.service         = service
        self.plan_mode       = plan_mode
        self.slack_webhook   = os.getenv("SLACK_WEBHOOK_URL")
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
        self.base_url        = os.getenv("REPORT_BASE_URL",
                                         "https://[username].github.io/stock-screener-reports")

    def format_message_free(self, selected: List[Dict], total_count: int,
                             html_path: str = "") -> str:
        """
        辟｡譁咏沿騾夂衍繝｡繝・そ繝ｼ繧ｸ・磯∈謚・莉ｶ・・

        Args:
            selected: 驕ｸ謚懊＆繧後◆3驫俶氛
            total_count: 蜈ｨ隧ｲ蠖馴釜譟・焚
            html_path: HTML繝ｬ繝昴・繝医・繝代せ・・ree_beta繝｢繝ｼ繝峨・縺ｿ・・
        """
        today = datetime.now().strftime('%Y蟷ｴ%m譛・d譌･')

        if not selected:
            return (
                f"投 譌･譛ｬ譬ｪ繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ邨先棡\n套 {today}\n\n"
                "這 譛ｬ譌･縺ｯ譚｡莉ｶ縺ｫ蜷郁・縺吶ｋ驫俶氛縺後≠繧翫∪縺帙ｓ縺ｧ縺励◆縲・n"
            )

        msg = (
            f"投 譌･譛ｬ譬ｪ繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ邨先棡 v3.0\n"
            f"套 {today}\n\n"
            f"識 譛ｬ譌･ {total_count}驫俶氛縺梧擅莉ｶ縺ｫ蜷郁・縺励∪縺励◆\n\n"
            f"縲蝉ｻ頑律縺ｮ豕ｨ逶ｮ3驫俶氛縲托ｼ井ｸｭ菴催怜ｮ牙ｮ壽姶逡･・噂n"
            f"{'笏'*40}\n\n"
        )

        for i, r in enumerate(selected, 1):
            # 繧ｷ繧ｰ繝翫Ν隕∫ｴ・
            signals = []
            if r['bb_reversal'] == '笨・: signals.append('BB蜿咲匱')
            if r['bb_breakout'] == '笨・: signals.append('BB繝悶Ξ繧､繧ｯ')
            if r['volume_surge'] == '笨・: signals.append('蜃ｺ譚･鬮俶･蠅・)
            if r['obv_trend_up'] == '笨・: signals.append('OBV荳頑・')
            if r['ichimoku_bullish'] != '窶・: signals.append(r['ichimoku_label'])

            signal_str = " | ".join(signals) if signals else "螳牙ｮ壽耳遘ｻ"

            msg += (
                f"{i}. 縲須r['code']}縲捜r['name']}\n"
                f"   箝・繧ｹ繧ｳ繧｢: {r['total_score']:.0f}轤ｹ  |  {r['sector']}\n"
                f"   跳 譬ｪ萓｡: ﾂ･{r['price']:,.0f}  |  {r['risk_tag']}\n"
                f"   投 {signal_str}\n\n"
            )

        # free_beta繝｢繝ｼ繝峨・蝣ｴ蜷医・HTML繝ｪ繝ｳ繧ｯ繧定ｿｽ蜉
        if self.plan_mode == "free_beta" and html_path:
            msg += (
                f"{'笏'*40}\n"
                f"塘 蜈ｨ{total_count}驫俶氛縺ｮ隧ｳ邏ｰ繝ｬ繝昴・繝医・縺薙■繧噂n"
                f"   {self.base_url}/{html_path}\n\n"
            )

        msg += (
            f"{'笏'*40}\n"
            f"虫 荳贋ｽ埼釜譟・ｂ隕九◆縺・婿縺ｯ\n"
            f"   痩 繝吶・繧ｷ繝・け繝励Λ繝ｳ ﾂ･980/譛・n"
            f"   痩 繝励Ξ繝溘い繝繝励Λ繝ｳ ﾂ･2,980/譛茨ｼ医メ繝｣繝ｼ繝井ｻ倥″・噂n"
        )

        return msg

    def format_message_full(self, results: List[Dict], sector_report: str = "",
                            html_path: str = "") -> str:
        """
        繝吶・繧ｷ繝・け繝ｻ繝励Ξ繝溘い繝逕ｨ騾夂衍・・TML繝ｪ繝ｳ繧ｯ驥崎ｦ厄ｼ・

        Args:
            results: 蜈ｨ繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ邨先棡
            html_path: HTML繝ｬ繝昴・繝医・繝代せ
        """
        today = datetime.now().strftime('%Y蟷ｴ%m譛・d譌･')
        plan_label = "繝励Ξ繝溘い繝繝励Λ繝ｳ" if self.plan_mode == "premium" else "繝吶・繧ｷ繝・け繝励Λ繝ｳ"

        if not results:
            return (
                f"投 譌･譛ｬ譬ｪ繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ邨先棡\n套 {today}\n\n"
                "這 譛ｬ譌･縺ｯ譚｡莉ｶ縺ｫ蜷郁・縺吶ｋ驫俶氛縺後≠繧翫∪縺帙ｓ縺ｧ縺励◆縲・n"
            )

        # Top 5縺ｮ繧ｵ繝槭Μ繝ｼ
        msg = (
            f"投 譌･譛ｬ譬ｪ繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ邨先棡 v3.0\n"
            f"套 {today}  |  {plan_label}\n\n"
            f"識 {len(results)}驫俶氛縺梧擅莉ｶ縺ｫ蜷郁・縺励∪縺励◆\n\n"
            f"縲慎op 5 繧ｵ繝槭Μ繝ｼ縲曾n"
            f"{'笏'*40}\n\n"
        )

        for i, r in enumerate(results[:5], 1):
            msg += (
                f"{i}. 縲須r['code']}縲捜r['name']}\n"
                f"   箝・{r['total_score']:.0f}轤ｹ  |  {r['sector']}\n"
                f"   跳 ﾂ･{r['price']:,.0f}  |  {r['risk_tag']}\n\n"
            )

        if len(results) > 5:
            msg += f"...莉本len(results)-5}驫俶氛\n\n"

        # HTML繝ｪ繝ｳ繧ｯ
        msg += (
            f"{'笏'*40}\n"
            f"塘 蜈ｨ{len(results)}驫俶氛縺ｮ隧ｳ邏ｰ繝ｬ繝昴・繝・n"
            f"   {self.base_url}/{html_path}\n\n"
        )

        # 繧ｻ繧ｯ繧ｿ繝ｼ繝ｬ繝昴・繝・
        if sector_report:
            msg += sector_report

        return msg

    def send_slack(self, message: str):
        """Slack騾∽ｿ｡"""
        if not self.slack_webhook:
            print("笞・・SLACK_WEBHOOK_URL 縺瑚ｨｭ螳壹＆繧後※縺・∪縺帙ｓ")
            return
        resp = requests.post(self.slack_webhook, json={"text": message})
        print("笨・Slack騾∽ｿ｡螳御ｺ・ if resp.status_code == 200
              else f"笶・Slack螟ｱ謨・ {resp.status_code}")

    def send_discord(self, message: str):
        """Discord騾∽ｿ｡・・000譁・ｭ怜宛髯仙ｯｾ蠢懶ｼ・""
        if not self.discord_webhook:
            print("笞・・DISCORD_WEBHOOK_URL 縺瑚ｨｭ螳壹＆繧後※縺・∪縺帙ｓ")
            return
        # 2000譁・ｭ怜宛髯舌・縺溘ａ蛻・牡騾∽ｿ｡
        chunks = [message[i:i+1900] for i in range(0, len(message), 1900)]
        for chunk in chunks:
            resp = requests.post(self.discord_webhook, json={"content": chunk})
            print("笨・Discord騾∽ｿ｡螳御ｺ・ if resp.status_code == 204
                  else f"笶・Discord螟ｱ謨・ {resp.status_code}")
            time.sleep(0.3)

    def notify(self, results: List[Dict], selected: List[Dict] = None,
               sector_report: str = "", html_path: str = ""):
        """
        騾夂衍繧帝∽ｿ｡・医・繝ｩ繝ｳ縺ｫ蠢懊§縺ｦ蛻・ｊ譖ｿ縺茨ｼ・

        Args:
            results: 蜈ｨ繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ邨先棡
            selected: 辟｡譁咏沿驕ｸ謚憺釜譟・ｼ・ree/free_beta繝｢繝ｼ繝峨・縺ｿ・・
            sector_report: 繧ｻ繧ｯ繧ｿ繝ｼ邨ｱ險・
            html_path: HTML繝ｬ繝昴・繝医・繝代せ
        """
        # 繝｡繝・そ繝ｼ繧ｸ逕滓・
        if self.plan_mode in ["free", "free_beta"]:
            if selected is None:
                print("笶・繧ｨ繝ｩ繝ｼ: 辟｡譁咏沿繝｢繝ｼ繝峨〒縺ｯ selected 縺悟ｿ・ｦ√〒縺・)
                return
            message = self.format_message_free(selected, len(results), html_path)
        else:
            message = self.format_message_full(results, sector_report, html_path)

        # 繧ｳ繝ｳ繧ｽ繝ｼ繝ｫ蜃ｺ蜉・
        print("\n" + "=" * 50)
        print(message)
        print("=" * 50 + "\n")

        # Webhook騾∽ｿ｡
        if self.service == "slack":
            self.send_slack(message)
        elif self.service == "discord":
            self.send_discord(message)

    def is_market_open() -> tuple[bool, str]:
        """
        譚ｱ莠ｬ險ｼ蛻ｸ蜿門ｼ墓園縺ｮ髢句ｴ譌･縺九←縺・°繧貞愛螳・
    
        Returns:
            (bool, str): (髢句ｴ縺九←縺・°, 逅・罰)
        """
        today = datetime.now()
    
        # 蝨滓屆譌･繝√ぉ繝・け
        if today.weekday() == 5:
            return False, "蝨滓屆譌･"
    
        # 譌･譖懈律繝√ぉ繝・け
        if today.weekday() == 6:
            return False, "譌･譖懈律"
    
        # 逾晄律繝√ぉ繝・け
        if jpholiday.is_holiday(today):
            holiday_name = jpholiday.is_holiday_name(today)
            return False, f"逾晄律・・holiday_name}・・
    
        # 蟷ｴ譛ｫ蟷ｴ蟋九・迚ｹ蛻･莨大ｴ譌･・・2/31, 1/2, 1/3・・
        if (today.month == 12 and today.day == 31) or \
           (today.month == 1 and today.day in [2, 3]):
           return False, "蟷ｴ譛ｫ蟷ｴ蟋倶ｼ大ｴ"
    
        return True, ""


def main():
    """繝｡繧､繝ｳ螳溯｡碁未謨ｰ v3.0 Final・・iscord・・""
    
    # 蟶ょｴ莨大ｴ譌･繝√ぉ繝・け
    is_open, reason = is_market_open()
    if not is_open:
        today = datetime.now().strftime('%Y蟷ｴ%m譛・d譌･')
        print(f"這 譛ｬ譌･・・today}・峨・{reason}縺ｮ縺溘ａ蟶ょｴ莨大ｴ縺ｧ縺・)
        print("投 繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ縺ｯ螳溯｡後＆繧後∪縺帙ｓ\n")
        
        # Discord 縺ｫ莨大ｴ騾夂衍・医が繝励す繝ｧ繝ｳ・・
        notification_service = os.getenv("NOTIFICATION_SERVICE", "discord")
        if notification_service == "discord":
            discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
            if discord_webhook:
                try:
                    message = {
                        "content": f"套 蟶ょｴ莨大ｴ縺ｮ縺顔衍繧峨○\n\n譛ｬ譌･・・today}・峨・{reason}縺ｮ縺溘ａ縲・
                                   f"譚ｱ莠ｬ險ｼ蛻ｸ蜿門ｼ墓園縺ｯ莨大ｴ縺ｧ縺吶・n"
                                   f"繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ縺ｯ谺｡蝗樣幕蝣ｴ譌･縺ｫ螳溯｡後＆繧後∪縺吶・
                    }
                    requests.post(discord_webhook, json=message)
                    print("笨・Discord 縺ｫ莨大ｴ騾夂衍繧帝∽ｿ｡縺励∪縺励◆")
                except Exception as e:
                    print(f"笞・・ Discord 騾夂衍繧ｨ繝ｩ繝ｼ: {e}")
        
        return
    
    print("噫 譌･譛ｬ蟶ょｴ蜈ｨ驫俶氛繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ髢句ｧ・v3.0 Final\n")
    print("討 騾夂衍: Discord\n")  # SendGrid 蜑企勁

    # 笏笏笏 迺ｰ蠅・､画焚隱ｭ縺ｿ霎ｼ縺ｿ 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    notification_service = os.getenv("NOTIFICATION_SERVICE", "slack")
    plan_mode            = os.getenv("PLAN_MODE", "free_beta")
    max_stocks           = os.getenv("MAX_STOCKS")
    enable_backtest      = os.getenv("ENABLE_BACKTEST", "true").lower() == "true"
    min_score            = float(os.getenv("MIN_SCORE", "30"))
    use_sample           = os.getenv("USE_SAMPLE", "false").lower() == "true"
    output_dir           = os.getenv("OUTPUT_DIR", "docs")

    print(f"笞呻ｸ・ 繝励Λ繝ｳ繝｢繝ｼ繝・ {plan_mode}")
    print(f"討 騾夂衍繧ｵ繝ｼ繝薙せ: {notification_service}")

    if max_stocks:
        max_stocks = int(max_stocks)
        print(f"笞・・ 繝・せ繝医Δ繝ｼ繝・ {max_stocks}驫俶氛縺ｮ縺ｿ繧ｹ繧ｭ繝｣繝ｳ\n")

    # 笏笏笏 繧ｹ繧ｯ繝ｪ繝ｼ繝九Φ繧ｰ螳溯｡・笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    screener = AdvancedStockScreener(
        min_volume      = 1_000_000,
        enable_backtest = enable_backtest,
        min_score       = min_score,
    )
    results = screener.scan_all_stocks(max_stocks=max_stocks, use_sample=use_sample)

    if not results:
        print("\n這 譚｡莉ｶ縺ｫ蜷郁・縺吶ｋ驫俶氛縺後≠繧翫∪縺帙ｓ縺ｧ縺励◆")
        return

    # 笏笏笏 繧ｻ繧ｯ繧ｿ繝ｼ繝ｬ繝昴・繝育函謌・笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    sector_report = screener.generate_sector_report()

    # 笏笏笏 繝励Λ繝ｳ縺ｫ蠢懊§縺溷・逅・笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    html_path = ""
    selected = []

    if plan_mode in ["free", "free_beta"]:
        # 辟｡譁咏沿・壻ｸｭ菴・莉ｶ繧帝∈謚・
        selected = screener.select_free_tier_stocks(results, count=3)
        print(f"\n識 辟｡譁咏沿・嘴len(selected)}驫俶氛繧帝∈謚懊＠縺ｾ縺励◆")
        for i, s in enumerate(selected, 1):
            print(f"  {i}. {s['code']} {s['name']} (繧ｹ繧ｳ繧｢:{s['total_score']:.0f}轤ｹ)")

    if plan_mode == "free_beta":
        # 證ｫ螳夂┌蜆溽沿・唏TML繝ｬ繝昴・繝育函謌・
        print("\n塘 HTML繝ｬ繝昴・繝育函謌蝉ｸｭ・域圻螳夂┌蜆溽沿・・..")
        html_gen = HTMLReportGenerator(output_dir=output_dir)
        today = datetime.now().strftime('%Y-%m-%d')
        html_path = html_gen.generate_basic_report(results, today, sector_report)
        html_gen.generate_index_page(html_path, len(results))

    elif plan_mode == "basic":
        # 繝吶・繧ｷ繝・け・唏TML繝ｬ繝昴・繝育函謌撰ｼ亥ｽ捺律縺ｮ縺ｿ・・
        print("\n塘 HTML繝ｬ繝昴・繝育函謌蝉ｸｭ・医・繝ｼ繧ｷ繝・け迚茨ｼ・..")
        html_gen = HTMLReportGenerator(output_dir=output_dir)
        today = datetime.now().strftime('%Y-%m-%d')
        html_path = html_gen.generate_basic_report(results, today, sector_report)
        html_gen.generate_index_page(html_path, len(results))

    elif plan_mode == "premium":
        # 繝励Ξ繝溘い繝・・0譌･蛻・い繝ｼ繧ｫ繧､繝・+ 繝√Ε繝ｼ繝育函謌撰ｼ亥ｰ・擂螳溯｣・ｼ・
        print("\n荘 繝励Ξ繝溘い繝迚医・蟆・擂螳溯｣・ｺ亥ｮ壹〒縺・)
        html_gen = HTMLReportGenerator(output_dir=output_dir)
        today = datetime.now().strftime('%Y-%m-%d')
        html_path = html_gen.generate_basic_report(results, today, sector_report)
        html_gen.generate_index_page(html_path, len(results))

    # 笏笏笏 騾夂衍騾∽ｿ｡ 笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏笏
    notifier = AdvancedNotifier(service=notification_service, plan_mode=plan_mode)

    if plan_mode in ["free", "free_beta"]:
        notifier.notify(results, selected=selected, sector_report=sector_report,
                        html_path=html_path)
    else:
        notifier.notify(results, sector_report=sector_report, html_path=html_path)

    print("\n笨・蜃ｦ逅・ｮ御ｺ・)


if __name__ == "__main__":
    main()

