import yfinance as yf
import pandas as pd
from datetime import datetime
import requests
import time

# ================== 你的設定 ==================
BOT_TOKEN = "8759654338:AAEZ2LKcFzbF3EBxMNIrz8EXIE8RyzPKJZc"
CHAT_ID = "8409795065"

# 大市值 + 恒生指數 + HSCEI + 恒生科技指數成分股
WATCHLIST = [
    # 恒生指數主要成分
    "0700.HK", "9988.HK", "0005.HK", "0941.HK", "1398.HK", "939.HK", "1299.HK",
    "1810.HK", "883.HK", "3988.HK", "1211.HK", "2318.HK", "0388.HK", "0001.HK",
    "0002.HK", "0003.HK", "0011.HK", "0016.HK", "0267.HK", "0857.HK", "1088.HK",
    "1288.HK", "3968.HK", "2628.HK",

    # 恒生中國企業指數 (HSCEI)
    "3690.HK", "9618.HK", "9888.HK", "1024.HK", "9999.HK", "9961.HK", "6869.HK",
    "1109.HK", "2313.HK", "2020.HK", "2269.HK", "6160.HK", "6690.HK", "9866.HK",
    "0981.HK", "1347.HK", "2018.HK",

    # 恒生科技指數 (HSTECH)
    "0700.HK", "9988.HK", "1810.HK", "3690.HK", "1211.HK", "1024.HK", "9888.HK",
    "9618.HK", "9999.HK", "9966.HK", "9868.HK", "2015.HK", "6690.HK", "0981.HK",
    "992.HK", "268.HK", "3888.HK", "285.HK", "20.HK", "241.HK", "1347.HK",
    "9626.HK", "300.HK", "780.HK", "9863.HK", "6618.HK"
]

VOLUME_MULTIPLIER = 1.5

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
        print(f"✅ 已發送 @ {datetime.now().strftime('%H:%M')}")
    except Exception as e:
        print(f"發送失敗: {e}")

def get_signals():
    signals = []
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M HKT")
    
    send_telegram(f"🚀 港股短線掃描 Agent 啟動 (每日 10:00 & 14:00)\n時間: {now_str}\n正在掃描 {len(WATCHLIST)} 隻重要股票...")

    for ticker in WATCHLIST:
        try:
            df = yf.download(ticker, period="3mo", interval="1d", progress=False)
            if len(df) < 50:
                continue
            
            df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
            df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
            df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
            df['VolAvg20'] = df['Volume'].rolling(20).mean()
            
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            golden_cross = (prev['EMA9'] <= prev['EMA21']) and (latest['EMA9'] > latest['EMA21'])
            volume_spike = latest['Volume'] > latest['VolAvg20'] * VOLUME_MULTIPLIER
            above_200ma = latest['Close'] > latest['EMA200']
            
            if golden_cross and volume_spike and above_200ma:
                change = ((latest['Close'] - prev['Close']) / prev['Close']) * 100
                signals.append(f"✅ <b>{ticker}</b>\n"
                               f"價格: ${latest['Close']:.2f} (+{change:.1f}%)\n"
                               f"成交量: {latest['Volume']/1e6:.1f}M (x{latest['Volume']/latest['VolAvg20']:.1f}倍)\n"
                               f"訊號: 9EMA 金叉 + 量能爆發")
        except:
            continue
    
    if signals:
        message = f"🔥 <b>短線買入訊號清單 ({len(signals)} 隻)</b>\n\n" + "\n\n".join(signals)
        send_telegram(message)
    else:
        send_telegram("📭 今日暫無符合 9/21 EMA + 成交量確認 買入訊號")

if __name__ == "__main__":
    print("短線掃描 Agent (每日 10:00 & 14:00) 已啟動...")
    
    while True:
        now = datetime.now()
        
        # 只喺周一至周五 10:00 或 14:00 附近運行 (±5 分鐘)
        if now.weekday() < 5:
            if (now.hour == 10 and 0 <= now.minute <= 5) or (now.hour == 14 and 0 <= now.minute <= 5):
                get_signals()
            else:
                # 每 30 分鐘只打印一次狀態，避免刷屏
                if now.minute % 30 == 0:
                    print(f"等待預設時間... 目前 {now.strftime('%H:%M')}")
        else:
            if now.minute % 30 == 0:
                print(f"周末，暫停掃描... {now.strftime('%H:%M')}")
        
        time.sleep(60)   # 每 60 秒檢查一次時間（更準確 + 安靜）