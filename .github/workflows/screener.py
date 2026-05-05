import pandas as pd
import requests
from datetime import datetime
import time
import subprocess
import re

print("🚀 오일전문가 스크리닝 시작\n")

headers = {'User-Agent': 'Mozilla/5.0'}
all_stocks = []

print("📊 KOSPI 종목 수집...", end='', flush=True)
for page in range(1, 25):
    try:
        url = f"https://finance.naver.com/sise/sise_market.nhn?gubun=0&page={page}"
        response = requests.get(url, headers=headers, timeout=5)
        codes = re.findall(r'code=(\d{6})', response.text)
        if codes:
            for code in codes:
                all_stocks.append({'code': code, 'market': 'KOSPI'})
        else:
            break
        time.sleep(0.2)
    except:
        break
print(f" ✓ ({len([s for s in all_stocks if s['market']=='KOSPI'])}개)")

print("📊 KOSDAQ 종목 수집...", end='', flush=True)
for page in range(1, 25):
    try:
        url = f"https://finance.naver.com/sise/sise_market.nhn?gubun=1&page={page}"
        response = requests.get(url, headers=headers, timeout=5)
        codes = re.findall(r'code=(\d{6})', response.text)
        if codes:
            for code in codes:
                if code not in [s['code'] for s in all_stocks]:
                    all_stocks.append({'code': code, 'market': 'KOSDAQ'})
        else:
            break
        time.sleep(0.2)
    except:
        break
print(f" ✓ ({len([s for s in all_stocks if s['market']=='KOSDAQ'])}개)")

unique_stocks = []
seen = set()
for s in all_stocks:
    if s['code'] not in seen:
        unique_stocks.append(s)
        seen.add(s['code'])

print(f"\n✅ {len(unique_stocks)}개 종목 수집 완료\n")

def fetch_data(code):
    try:
        url = f"https://finance.naver.com/item/main.nhn?code={code}"
        response = requests.get(url, headers=headers, timeout=2)
        if response.status_code == 200:
            per = re.search(r'PER.*?(\d+\.\d+)', response.text)
            pbr = re.search(r'PBR.*?(\d+\.\d+)', response.text)
            div = re.search(r'배당수익률.*?(\d+\.\d+)%', response.text)
            name = re.search(r'<title>([^<]+)', response.text)
            return {
                'code': code,
                'name': name.group(1).split('-')[0].strip() if name else f'종목_{code}',
                'per': float(per.group(1)) if per else 0,
                'pbr': float(pbr.group(1)) if pbr else 0,
                'div': float(div.group(1)) if div else 0
            }
    except:
        pass
    return None

def score(data):
    s = 0
    div = data.get('div', 0)
    per = data.get('per', 0)
    pbr = data.get('pbr', 0)
    if div > 5: s += 20
    elif div > 3: s += 15
    elif div > 0: s += 10
    else: s += 5
    if 0 < per < 8: s += 20
    elif per < 12: s += 15
    elif per > 0: s += 5
    if 0 < pbr < 0.6: s += 15
    elif pbr < 1.0: s += 10
    elif pbr > 0: s += 5
    return s, 'A' if s > 45 else 'B' if s > 35 else 'C' if s > 25 else 'D'

print(f"📈 {len(unique_stocks)}개 종목 분석 중...\n")
results = []

for idx, stock in enumerate(unique_stocks):
    if (idx + 1) % 500 == 0:
        print(f"[{idx+1}/{len(unique_stocks)}] 진행 중...")
    data = fetch_data(stock['code'])
    if data:
        s, g = score(data)
        results.append({
            '순위': 0,
            '종목코드': stock['code'],
            '종목명': data['name'],
            '시장': stock['market'],
            '배당수익률(%)': round(data['div'], 1),
            'PER': round(data['per'], 1) if data['per'] > 0 else 'N/A',
            'PBR': round(data['pbr'], 2) if data['pbr'] > 0 else 'N/A',
            '총점': s,
            '등급': g,
            '업데이트': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    time.sleep(0.05)

df = pd.DataFrame(results)
df = df.sort_values('총점', ascending=False).reset_index(drop=True)
df.insert(0, '순위', range(1, len(df) + 1))

print(f"\n✅ {len(df)}개 분석 완료")
print(f"A등급: {len(df[df['등급']=='A'])}개 | B등급: {len(df[df['등급']=='B'])}개")
print(f"C등급: {len(df[df['등급']=='C'])}개 | D등급: {len(df[df['등급']=='D'])}개\n")

with open('data.csv', 'w', encoding='utf-8-sig') as f:
    f.write(df.to_csv(index=False, encoding='utf-8-sig'))

subprocess.run(['git', 'config', 'user.email', 'action@github.com'])
subprocess.run(['git', 'config', 'user.name', 'GitHub Action'])
subprocess.run(['git', 'add', 'data.csv'])
subprocess.run(['git', 'commit', '-m', f'Update - {len(df)} stocks'])
subprocess.run(['git', 'push'])

print("✅ GitHub 업로드 완료!")            name = name_match.group(1).split('-')[0].strip() if name_match else f'종목_{code}'
            
            return {
                'per': per,
                'pbr': pbr,
                'dividend_yield': div,
                'name': name
            }
    except:
        pass
    
    return None

# 채점
def score_stock(data):
    score = 0
    
    div = data.get('dividend_yield', 0)
    if div > 5: score += 20
    elif div > 3: score += 15
    elif div > 0: score += 10
    else: score += 5
    
    per = data.get('per', 0)
    if 0 < per < 8: score += 20
    elif per < 12: score += 15
    else: score += 5
    
    pbr = data.get('pbr', 0)
    if 0 < pbr < 0.6: score += 15
    elif pbr < 1.0: score += 10
    else: score += 5
    
    if score > 45: grade = 'A'
    elif score > 35: grade = 'B'
    elif score > 25: grade = 'C'
    else: grade = 'D'
    
    return score, grade

# 메인
stocks = get_all_stocks()

print(f"📈 {len(stocks)}개 종목 분석 중...")
results = []

for idx, stock in enumerate(stocks):
    if (idx + 1) % 100 == 0:
        print(f"[{idx+1}/{len(stocks)}]")
    
    data = fetch_stock_data(stock['code'])
    
    if data:
        score, grade = score_stock(data)
        results.append({
            '순위': 0,
            '종목코드': stock['code'],
            '종목명': data['name'],
            '시장': stock['market'],
            '배당수익률(%)': round(data['dividend_yield'], 1),
            'PER': round(data['per'], 1) if data['per'] > 0 else 'N/A',
            'PBR': round(data['pbr'], 2) if data['pbr'] > 0 else 'N/A',
            '총점': score,
            '등급': grade,
            '업데이트': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    time.sleep(0.1)

results_df = pd.DataFrame(results)
results_df = results_df.sort_values('총점', ascending=False).reset_index(drop=True)
results_df.insert(0, '순위', range(1, len(results_df) + 1))

print(f"\n✅ {len(results_df)}개 종목 분석 완료")
print(f"A등급: {len(results_df[results_df['등급']=='A'])}개")
print(f"B등급: {len(results_df[results_df['등급']=='B'])}개")
print(f"C등급: {len(results_df[results_df['등급']=='C'])}개")
print(f"D등급: {len(results_df[results_df['등급']=='D'])}개\n")

# CSV 저장
csv_content = results_df.to_csv(index=False, encoding='utf-8-sig')

with open('data.csv', 'w', encoding='utf-8-sig') as f:
    f.write(csv_content)

# GitHub 커밋
import subprocess
subprocess.run(['git', 'config', 'user.email', 'action@github.com'])
subprocess.run(['git', 'config', 'user.name', 'GitHub Action'])
subprocess.run(['git', 'add', 'data.csv'])
subprocess.run(['git', 'commit', '-m', f'Update screener - {datetime.now()}'])
subprocess.run(['git', 'push'])

print("✅ 모든 작업 완료!")
