import base64
import hashlib
import json
import time
import uuid

import aiohttp


class ModulBankApi:
    BASE_URL = "https://pay.modulbank.ru/api/v1/bill"

    def __init__(
        self,
        merchant_id: str,
        secret_key: str,
        callback_url: str,
        success_url: str,
        testing: bool = False,
    ):
        self.merchant_id = merchant_id
        self.secret_key = secret_key
        self.callback_url = callback_url
        self.success_url = success_url
        self.testing = testing

    async def get_payment_uri(self, order_data: dict) -> str:
        """
        Отправляет запрос к ModulBank для получения ссылки на оплату.
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(self.BASE_URL, json=order_data) as response:
                response.raise_for_status()
                data = await response.json()
                return data["bill"]["url"]

    def prepare_content(self, order_id: str, amount: int, user_id: int) -> dict:
        """
        Подготавливает данные для запроса к ModulBank.
        """
        items = [
            {
                "name": "Пополнение баланса бота Reader",
                "quantity": 1,
                "sno": "usn_income",
                "payment_object": "service",
                "payment_method": "full_prepayment",
                "vat": "none",
                "price": amount,
            }
        ]

        description = f"Пополнение баланса бота Reader для пользователя {user_id}"

        payload = {
            "merchant": self.merchant_id,
            "amount": str(amount),
            "description": description,
            "lifetime": str(30 * 60),
            "receipt_items": json.dumps(items, ensure_ascii=False),
            "unix_timestamp": str(time.time()).split(".")[0],
            "salt": str(uuid.uuid4()).split("-")[0],
            "custom_order_id": order_id,
            "callback_url": self.callback_url,
            "success_url": self.success_url,
        }

        if self.testing:
            payload["testing"] = "1"

        payload["signature"] = self.get_signature(payload)
        return payload

    def get_signature(self, form_data: dict) -> str:
        """
        Генерирует подпись для запроса.
        """
        filtered_data = {k: v for k, v in form_data.items() if v and k != "signature"}
        sorted_data = sorted(filtered_data.items())
        encoded_data = "&".join(f"{k}={self.get_base64_val(v)}" for k, v in sorted_data)
        signature = self.sha1(
            self.secret_key + self.sha1(self.secret_key + encoded_data)
        )
        return signature

    @staticmethod
    def get_base64_val(value: str) -> str:
        """
        Кодирует значение в Base64.
        """
        return base64.b64encode(value.encode("utf-8")).decode("utf-8")

    @staticmethod
    def sha1(value: str) -> str:
        """
        Генерирует SHA1-хэш.
        """
        hash_bytes = hashlib.sha1(value.encode("utf-8")).digest()
        return "".join(f"{b:02x}" for b in hash_bytes)
