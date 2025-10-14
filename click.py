from playwright.sync_api import sync_playwright
import time
import random
import traceback

def make_context_and_page(p, headless=True):
    browser = p.chromium.launch(headless=headless)
    context = browser.new_context(
        ignore_https_errors=True,
        user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    )
    context.route("**/*.{png,jpg,jpeg,gif,webp,css}", lambda route: route.abort())
    page = context.new_page()
    return browser, context, page

def refresh_loop(url, interval=0.001, run_forever=True, refresh_count=1000, headless=True):
    
    with sync_playwright() as p:
        browser, context, page = None, None, None
        attempt = 0
        i = 0

        def recreate():
            nonlocal browser, context, page
            try:
                if browser:
                    try:
                        browser.close()
                    except Exception:
                        pass
            except Exception:
                pass
            browser, context, page = make_context_and_page(p, headless=headless)
            return browser, context, page

        recreate()

        try:
            print("[+] First trial to navigate to :", url)
            try:
                page.goto(url, wait_until='domcontentloaded', timeout=15000)
            except Exception as e:
                print("[-] Fail to navigate :", e)
        except KeyboardInterrupt:
            print("[*] Unknown Error. Shuting Down.")
            return

        try:
            while True:
                if not run_forever and i >= refresh_count:
                    print("[*] Finished nvigating. This will automatically close.")
                    break

                try:
                    if i % 10 == 0:
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] refresh {i+1}" +
                              ("" if run_forever else f"/{refresh_count}"))
                    page.reload(wait_until='commit', timeout=15000)

                    sleep_t = max(0.001, interval + random.uniform(-interval*0.2, interval*0.2))
                    time.sleep(sleep_t)
                    i += 1
                    attempt = 0
                except KeyboardInterrupt:
                    print("[*] Finishing.")
                    break
                except Exception as e:
                    print(f"[-] Error Refreshing : {e}")
                    traceback.print_exc()
                    attempt += 1

                    msg = str(e).lower()
                    if 'closed' in msg or 'target' in msg or attempt >= 1:
                        print("[*] Re-opening Browser (attempt {}).".format(attempt))
                        backoff = min(30, 1 + attempt * 2)
                        time.sleep(backoff)
                        try:
                            recreate()
                            try:
                                page.goto(url, wait_until='domcontentloaded', timeout=15000)
                                print("[+] Accessed to Re-open.")
                            except Exception as e2:
                                print("[-] Fail to Re-open :", e2)
                        except Exception as e3:
                            print("[-] Exception on Re-open :", e3)
                            time.sleep(1.5)
                    else:
                        time.sleep(1)

        finally:
            try:
                if browser:
                    browser.close()
            except Exception:
                pass
            print("[+] Finish Successfully. Shuting automatically.")

if __name__ == "__main__":
    url = input("Please enter the URL to refresh: ")
    refresh_loop(
        url,
        interval=0.001,
        run_forever=True
    )