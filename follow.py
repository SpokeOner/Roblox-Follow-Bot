# https://github.com/SpokeOner 
import time
import hashlib
import base64
import json
import random
from random import choice, shuffle, uniform, randint
from threading import Thread, Lock
from typing import Dict, Tuple, List, Optional
from curl_cffi import Session
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from colorama import Fore, Style


class AuthTokenGenerator:
    @staticmethod
    def _to_bytes(text: str) -> bytes:
        return text.encode('utf-8')

    @staticmethod
    def _b64_encode(data: bytes) -> str:
        return base64.b64encode(data).decode('ascii')

    @staticmethod
    def generate_token(payload: str, endpoint: str, http_method: str) -> str:
        payload_bytes = payload.encode('utf-8')
        hash_digest = hashlib.sha256(payload_bytes).digest()
        encoded_hash = AuthTokenGenerator._b64_encode(hash_digest)

        current_time = str(int(time.time()))
        key_pair = ec.generate_private_key(ec.SECP256R1(), default_backend())

        sig_data = f"{encoded_hash}|{current_time}|{endpoint}|{http_method.upper()}"
        sig_bytes = key_pair.sign(
            AuthTokenGenerator._to_bytes(sig_data),
            ec.ECDSA(hashes.SHA256())
        )
        r_val, s_val = decode_dss_signature(sig_bytes)
        sig_raw = r_val.to_bytes(32, 'big') + s_val.to_bytes(32, 'big')
        encoded_sig1 = AuthTokenGenerator._b64_encode(sig_raw)

        path_suffix = endpoint.split('.com')[1] if '.com' in endpoint else endpoint
        sig_data2 = f"|{current_time}|{path_suffix}|{http_method.upper()}"
        sig_bytes2 = key_pair.sign(
            AuthTokenGenerator._to_bytes(sig_data2),
            ec.ECDSA(hashes.SHA256())
        )
        r_val2, s_val2 = decode_dss_signature(sig_bytes2)
        sig_raw2 = r_val2.to_bytes(32, 'big') + s_val2.to_bytes(32, 'big')
        encoded_sig2 = AuthTokenGenerator._b64_encode(sig_raw2)

        return f"v1|{encoded_hash}|{current_time}|{encoded_sig1}|{encoded_sig2}"


class RobloxClient:
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    ]

    def __init__(self):
        self.token_gen = AuthTokenGenerator()

    def _get_headers(self) -> Dict[str, str]:
        return {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'origin': 'https://www.roblox.com',
            'referer': 'https://www.roblox.com/',
            'user-agent': choice(self.USER_AGENTS),
            'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="121", "Google Chrome";v="121"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
        }

    def _setup_session_cookies(self, auth_cookie: str, session: Session) -> None:
        session.allow_redirects = True
        session.cookies.set(".ROBLOSECURITY", auth_cookie, ".roblox.com", "/", secure=True)
        response = session.get("https://roblox.com", timeout=10)
        session.cookies.update(response.cookies)
        time.sleep(uniform(0.5, 1.5))

    def _obtain_csrf_token(self, session: Session) -> Optional[str]:
        endpoint = "https://friends.roblox.com/v1/users/1/follow"
        try:
            response = session.post(endpoint, timeout=10)
            csrf_token = response.headers.get("x-csrf-token")
            if csrf_token:
                session.headers.update({"x-csrf-token": csrf_token})
                return csrf_token
        except Exception as e:
            pass
        return None

    def _parse_error_reason(self, response_text: str, status_code: int) -> str:
        if not response_text:
            if status_code == 403:
                return "Forbidden - Possible rate limit or captcha"
            elif status_code == 401:
                return "Unauthorized - Invalid cookie"
            elif status_code == 404:
                return "User not found"
            elif status_code == 429:
                return "Rate limited"
            else:
                return f"HTTP {status_code} error"
        
        try:
            error_data = json.loads(response_text)
            if isinstance(error_data, dict):
                if "errors" in error_data and error_data["errors"]:
                    error_msg = error_data["errors"][0].get("message", "")
                    if error_msg:
                        return error_msg[:60]
                if "message" in error_data:
                    return error_data["message"][:60]
                if "error" in error_data:
                    return str(error_data["error"])[:60]
        except:
            pass
        
        response_lower = response_text.lower()
        if "captcha" in response_lower or "challenge" in response_lower:
            return "Captcha required"
        elif "rate limit" in response_lower or "too many" in response_lower:
            return "Rate limited"
        elif "unauthorized" in response_lower or "invalid" in response_lower:
            return "Invalid authentication"
        elif "not found" in response_lower:
            return "User not found"
        elif "already" in response_lower:
            return "Already following user"
        
        return response_text[:60] if len(response_text) > 60 else response_text

    def execute_follow(self, auth_cookie: str, proxy_addr: str, target_user_id: str) -> Tuple[str, bool, str, int]:
        client_session = Session(
            impersonate="safari",
            default_headers=True,
            proxy=proxy_addr,
            timeout=15
        )

        client_session.headers.update(self._get_headers())

        api_endpoint = f"https://friends.roblox.com/v1/users/{target_user_id}/follow"
        auth_token = self.token_gen.generate_token("", api_endpoint, "post")
        client_session.headers.update({"x-bound-auth-token": auth_token})

        try:
            self._setup_session_cookies(auth_cookie, client_session)
            
            csrf = self._obtain_csrf_token(client_session)
            if not csrf:
                client_session.close()
                return ("CSRF token retrieval failed", False, "", 0)

            time.sleep(uniform(0.3, 0.8))

            response = client_session.post(api_endpoint, timeout=15)
            status_code = response.status_code
            response_text = response.text
            client_session.close()

            if status_code == 200:
                return ("SUCCESS", True, response_text, status_code)
            else:
                error_reason = self._parse_error_reason(response_text, status_code)
                return (error_reason, False, response_text, status_code)
        except Exception as e:
            try:
                client_session.close()
            except:
                pass
            error_msg = str(e)
            if "timeout" in error_msg.lower():
                return ("Connection timeout", False, "", 0)
            elif "proxy" in error_msg.lower():
                return ("Proxy connection failed", False, "", 0)
            else:
                return (f"Network error: {error_msg[:40]}", False, "", 0)

# https://github.com/SpokeOner

class PerformanceTracker:
    def __init__(self):
        self.lock = Lock()
        self.completed = 0
        self.failed = 0
        self.start_time = time.time()

    def increment_success(self):
        with self.lock:
            self.completed += 1

    def increment_failure(self):
        with self.lock:
            self.failed += 1

    def get_rate(self) -> float:
        elapsed = time.time() - self.start_time
        minutes = elapsed / 60.0
        if minutes == 0:
            return 0.0
        return round(self.completed / minutes, 2)

    def get_stats(self) -> Tuple[int, int, float]:
        with self.lock:
            return self.completed, self.failed, self.get_rate()


def load_resources() -> Tuple[List[str], List[str]]:
    try:
        with open("input/proxies.txt", "r", encoding="utf-8") as f:
            proxy_list = [p.strip() for p in f.read().splitlines() if p.strip()]
    except FileNotFoundError:
        proxy_list = []
    
    try:
        with open("input/cookies.txt", "r", encoding="utf-8") as f:
            cookie_list = [c.strip() for c in f.read().splitlines() if c.strip()]
    except FileNotFoundError:
        cookie_list = []

    shuffle(cookie_list)
    return proxy_list, cookie_list


def distribute_items(items: List, num_workers: int) -> List[List]:
    if num_workers <= 0:
        return [items]
    
    chunk_size = len(items) / num_workers
    result = []
    current_pos = 0.0
    
    while current_pos < len(items):
        end_pos = int(current_pos + chunk_size)
        result.append(items[int(current_pos):end_pos])
        current_pos += chunk_size
    
    return result


def process_batch(cookie_batch: List[str], user_id: str, tracker: PerformanceTracker, proxy_pool: List[str]):
    client = RobloxClient()
    
    for auth_cookie in cookie_batch:
        max_retries = 3
        retry_count = 0
        succeeded = False
        
        while retry_count < max_retries and not succeeded:
            try:
                selected_proxy = choice(proxy_pool) if proxy_pool else None
                request_start = time.time()
                
                result_msg, success, response_data, status_code = client.execute_follow(
                    auth_cookie, selected_proxy, user_id
                )
                
                request_time = round(time.time() - request_start, 2)
                
                if success:
                    tracker.increment_success()
                    completed, failed, rate = tracker.get_stats()
                    print(f"{Fore.GREEN}Success{Style.RESET_ALL} | User: {user_id} | Time: {request_time}s | Done: {completed} | {rate}/min")
                    succeeded = True
                else:
                    retry_count += 1
                    tracker.increment_failure()
                    completed, failed, rate = tracker.get_stats()
                    status_info = f"{status_code}" if status_code > 0 else "N/A"
                    print(f"{Fore.RED}Failed{Style.RESET_ALL} | User: {user_id} | Try {retry_count}/{max_retries} | Status: {status_info} | Reason: {result_msg} | Failed: {failed} | {rate}/min")
                    
                    if retry_count < max_retries:
                        delay = uniform(1.0, 2.5) * retry_count
                        time.sleep(delay)
                        
            except Exception as e:
                retry_count += 1
                tracker.increment_failure()
                completed, failed, rate = tracker.get_stats()
                error_msg = str(e)[:40]
                print(f"{Fore.RED}Error{Style.RESET_ALL} | User: {user_id} | Try {retry_count}/{max_retries} | {error_msg} | Failed: {failed} | {rate}/min")
                if retry_count < max_retries:
                    time.sleep(uniform(0.5, 1.5))
        
        if not succeeded:
            time.sleep(uniform(0.2, 0.6))


def main():
    proxy_pool, cookie_pool = load_resources()
    
    if not cookie_pool:
        print("No cookies found")
        return
    
    try:
        thread_count = int(input("Enter thread count: "))
        target_user = input("Enter user id: ")
    except (ValueError, KeyboardInterrupt):
        return
    
    if thread_count <= 0:
        thread_count = 1
    
    print(f"\nStarting {thread_count} threads with {len(cookie_pool)} cookies\n")
    
    tracker = PerformanceTracker()
    batches = distribute_items(cookie_pool, thread_count)
    worker_threads = []
    
    for batch in batches:
        if batch:
            thread = Thread(
                target=process_batch,
                args=(batch, target_user, tracker, proxy_pool)
            )
            worker_threads.append(thread)
            thread.start()
            time.sleep(uniform(0.1, 0.3))
    
    for thread in worker_threads:
        thread.join()
    
    final_completed, final_failed, final_rate = tracker.get_stats()
    total_attempts = final_completed + final_failed
    success_rate = (final_completed / total_attempts * 100) if total_attempts > 0 else 0
    
    print(f"\nDone | Success: {final_completed} | Failed: {final_failed} | Total: {total_attempts} | Rate: {success_rate:.1f}% | {final_rate}/min")


if __name__ == "__main__":
    main()

# https://github.com/SpokeOner