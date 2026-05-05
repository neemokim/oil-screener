import gspread
import pandas as pd
import requests
from datetime import datetime
import os
import time

SHEET_ID = os.getenv('SHEET_ID', '1WYyBc1Jfm_oPCkyTfVJzDf9eoRfbgj0dyPm4cdClwDc')
SHEET_NAME = "스크리닝결과"

print("🚀 오일전문가 스크리닝 시작...\n")

# 모든 코스피 + 코스닥 종목 크롤링
def get_all_stocks():
    """네이버 금융에서 모든 종목 가져오기"""
    print("📊 전체 종목 데이터 수집 중...")
    
    stocks = []
    
    # KOSPI 종목
    try:
        url = "https://finance.naver.com/sise/sise_market.nhn?gubun=0"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        for page in range(1, 20):  # 최대 19페이지 (약 950개)
            print(f"  KOSPI 페이지 {page}...", end=' ')
            
            params = {'page': page}
            response = requests.get(url, headers=headers, params=params, timeout=5)
            
            if response.status_code == 200:
                import re
                # 종목코드와 이름 추출
                code_matches = re.findall(r'code=(\d+)', response.text)
                name_matches = re.findall(r'title="([^"]+)"', response.text)
                
                if code_matches:
                    for code in code_matches[:30]:  # 페이지당 약 30개
                        stocks.append({'code': code, 'name': f'종목_{code}', 'market': 'KOSPI'})
                    print("✓")
                else:
                    break
            else:
                break
            
            time.sleep(0.5)
    except Exception as e:
        print(f"KOSPI 수집 실패: {e}")
    
    # KOSDAQ 종목
    try:
        url = "https://finance.naver.com/sise/sise_market.nhn?gubun=1"
        
        for page in range(1, 20):
            print(f"  KOSDAQ 페이지 {page}...", end=' ')
            
            params = {'page': page}
            response = requests.get(url, headers=headers, params=params, timeout=5)
            
            if response.status_code == 200:
                import re
                code_matches = re.findall(r'code=(\d+)', response.text)
                
                if code_matches:
                    for code in code_matches[:30]:
                        stocks.append({'code': code, 'name': f'종목_{code}', 'market': 'KOSDAQ'})
                    print("✓")
                else:
                    break
            else:
                break
            
            time.sleep(0.5)
    except Exception as e:
        print(f"KOSDAQ 수집 실패: {e}")
    
    print(f"✅ 총 {len(stocks)}개 종목 수집 완료\n")
    return stocks

# 종목 정보 크롤링
def fetch_stock_data(code):
    """개별 종목 데이터"""
    try:
        url = f"https://finance.naver.com/item/main.nhn?code={code}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=3)
        
        if response.status_code == 200:
            import re
            
            per_match = re.search(r'PER.*?(\d+\.\d+)', response.text)
            pbr_match = re.search(r'PBR.*?(\d+\.\d+)', response.text)
            div_match = re.search(r'배당수익률.*?(\d+\.\d+)%', response.text)
            name_match = re.search(r'<title>([^<]+)', response.text)
            
            per = float(per_match.group(1)) if per_match else 0
            pbr = float(pbr_match.group(1)) if pbr_match else 0
            div = float(div_match.group(1)) if div_match else 0
            name = name_match.group(1).split('-')[0].strip() if name_match else f'종목_{code}'
            
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
