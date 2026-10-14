# -*- coding: utf-8 -*-
# runner.py - BULUT ORDUSU SİBER MOTORU

import os
import sys
import time
import uuid
import re
import random
import urllib.request
from playwright.sync_api import sync_playwright

# BİK v2 ve Geolocation İllüzyon Havuzları
TR_GENIS_CIHAZ_HAVUZU = [
    {"brand": "Samsung", "model": "Galaxy S23 Ultra (WebView)", "vw": 384, "vh": 854, "ram": 12, "cores": 8, "dpr": 3.75, "ua": "Mozilla/5.0 (Linux; Android 13; SM-S918B; Build/TP1A.220624.014) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/144.0.0.0 Mobile Safari/537.36"},
    {"brand": "Samsung", "model": "Galaxy A54 5G (WebView)", "vw": 412, "vh": 915, "ram": 8, "cores": 8, "dpr": 3.0, "ua": "Mozilla/5.0 (Linux; Android 13; SM-A546B; Build/TP1A.220624.014) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/144.0.0.0 Mobile Safari/537.36"},
    {"brand": "Xiaomi", "model": "Redmi Note 12 Pro (WebView)", "vw": 393, "vh": 873, "ram": 8, "cores": 8, "dpr": 2.75, "ua": "Mozilla/5.0 (Linux; Android 13; 22101316G; Build/TP1A.220624.014) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/144.0.0.0 Mobile Safari/537.36"}
]

PC_OS_HAVUZU = [
    {"brand": "ASUS", "model": "ASUS ROG Strix Windows 11", "vw": 1920, "vh": 1080, "ram": 32, "cores": 16, "dpr": 1.0, "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"}
]

def run_bullet_hit(site_url):
    profile_path = os.path.join(os.getcwd(), f"user_data_{uuid.uuid4().hex[:6]}")
    
    cihaz = "MOBIL" if random.random() < 0.93 else "PC"
    if_mobile = (cihaz == "MOBIL")
    selected_device = random.choice(TR_GENIS_CIHAZ_HAVUZU) if if_mobile else random.choice(PC_OS_HAVUZU)
    
    with sync_playwright() as p:
        args_list = [
            "--disable-blink-features=AutomationControlled", 
            "--no-sandbox", 
            "--disable-web-security", 
            "--ignore-certificate-errors"
        ]
        
        context = p.chromium.launch_persistent_context(
            user_data_dir=profile_path,
            headless=True,
            args=args_list,
            user_agent=selected_device["ua"],
            locale="tr-TR",
            timezone_id="Europe/Istanbul",
            viewport={"width": selected_device["vw"], "height": selected_device["vh"]},
            is_mobile=if_mobile,
            has_touch=if_mobile
        )
        
        page = context.new_page()
        
        # BİK v2 Doğrudan Giriş Simülasyonu
        target_link = site_url.strip()
        if not (target_link.startswith("http://") or target_link.startswith("https://")):
            target_link = f"https://target_link"

        def custom_route_handler(route, req):
            url_str = req.url.lower()
            
            # 🎯 GOOGLE ANALYTICS KATI KAYSERİ KONUM ENJEKSİYONU
            if ("google-analytics" in url_str or "/g/collect" in url_str) and "collect" in url_str:
                modified_url = req.url
                modified_url = re.sub(r'&geoid=[^&]*', '', modified_url)
                p_char = "&" if "?" in modified_url else "?"
                modified_url += f"{p_char}geoid=1014313&ul=tr-tr&_geo=1&gclid=AKINCI_BULUT_GEO&_pci=9067980"
                
                headers = {k: v for k, v in req.headers.items()}
                headers["X-GA-GeoIP-Bypass"] = "38.6946,35.5574"
                route.continue_(url=modified_url, headers=headers)
                return
            
            # 🎯 MICROSOFT CLARITY KURUMSAL YANILTMA
            if "clarity" in url_str and "collect" in url_str:
                modified_url = req.url
                p_char = "&" if "?" in modified_url else "?"
                modified_url += f"{p_char}_ack=1&cl_ee=1&_ms_enterprise=true&_trust_token={uuid.uuid4().hex.upper()}"
                
                headers = {k: v for k, v in req.headers.items()}
                headers["X-Clarity-Enterprise"] = "True"
                headers["Cookie"] = f"MUID={uuid.uuid4().hex.upper()}; CLARITY=1; MS_TRUST=1; _cl_trust=true"
                route.continue_(url=modified_url, headers=headers)
                return
            
            if "clarity" in url_str and "clarity.js" in url_str:
                try:
                    req_mod = urllib.request.Request(req.url, headers={'User-Agent': selected_device["ua"]})
                    with urllib.request.urlopen(req_mod, timeout=10) as response:
                        original_js = response.read().decode('utf-8')
                    
                    mutated_js = original_js.replace("isBot", "function(){return false}")
                    mutated_js = mutated_js.replace("navigator.webdriver", "undefined")
                    mutated_js = mutated_js.replace("document.hasFocus()", "true")
                    mutated_js = mutated_js.replace("botDetection:true", "botDetection:false")
                    
                    route.fulfill(status=200, content_type="application/javascript", body=mutated_js)
                    return
                except:
                    pass
            
            route.continue_()

        page.route("**/*", custom_route_handler)
        
        # Geolocation ve Donanım Kalkanı Enjeksiyonu
        js_payload = """
            (function(ram, cores, dpr) {
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'deviceMemory', {get: () => ram});
                Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => cores});
                Object.defineProperty(window, 'devicePixelRatio', {get: () => dpr});
                document.hasFocus = function() { return true; };
                
                navigator.geolocation.getCurrentPosition = function(success) {
                    success({
                        coords: { latitude: 38.6946, longitude: 35.5574, accuracy: 10.0 },
                        timestamp: Date.now()
                    });
                };
            })(8, 8, 3.0);
        """
        page.add_init_script(js_payload)
        
        print(f"[AĞ] Bulut Bilgisayarı Tetiklendi -> Hedef: {target_link}")
        page.goto(target_link, timeout=60000, wait_until="networkidle")
        
        # BİK v2 Süre Barajı (Kayseri için Organik Kalma Süresi)
        stay_time = random.randint(48, 58)
        print(f"[SÜRE] Sayfada {stay_time} saniye organik bekleniyor...")
        time.sleep(stay_time)
        
        # BİK v2 Sayfa Derinliği (Rastgele İç Sayfaya Tıklama)
        try:
            clean_domain = site_url.replace("https://", "").replace("http://", "").replace("www.", "").split('/')[0]
            inner_links = page.locator(f"a[href*='{clean_domain}']").all()
            valid_links = [lk for lk in inner_links if lk.get_attribute("href") and "#" not in str(lk.get_attribute("href"))]
            if len(valid_links) > 0:
                selected_link = random.choice(valid_links[:5])
                selected_link.scroll_into_view_if_needed()
                print("[DERİNLİK] İkinci sayfaya geçiş yapılıyor...")
                selected_link.click(timeout=5000, force=True)
                time.sleep(random.randint(15, 25))
        except Exception as e:
            print(f"[İÇ SAYFA] Derinlik atlanamadı: {str(e)}")
            
        context.close()

if __name__ == "__main__":
    # Çevre değişkeninden hedef siteyi oku, yoksa boş dön
    target_site = os.environ.get("TARGET_SITE", "")
    if target_site:
        run_bullet_hit(target_site)
