# Unit tests
import unittest
import dotenv

from aes256cipher import AES256Cipher


class TestAES256Cipher(unittest.TestCase):
    def setUp(self):
        self.cipher = AES256Cipher(dotenv.get("AUTH_KEY"))

    def test_encrypt_decrypt(self):
        original_text = "Hello, World!"
        encrypted = self.cipher.encrypt(original_text)
        decrypted = self.cipher.decrypt(encrypted)
        self.assertEqual(original_text, decrypted)

    def test_long_text(self):
        original_text = "This is a much longer text that spans multiple lines.\n" * 10
        encrypted = self.cipher.encrypt(original_text)
        decrypted = self.cipher.decrypt(encrypted)
        self.assertEqual(original_text, decrypted)

    def test_different_keys(self):
        original_text = "Secret message"
        cipher1 = AES256Cipher("key1")
        cipher2 = AES256Cipher("key2")
        encrypted = cipher1.encrypt(original_text)
        with self.assertRaises(Exception):
            cipher2.decrypt(encrypted)

    def test_empty_string(self):
        original_text = ""
        encrypted = self.cipher.encrypt(original_text)
        decrypted = self.cipher.decrypt(encrypted)
        self.assertEqual(original_text, decrypted)

    def test_decode_data(self):
        original_text = "SMS\nMessage: 63385 — ваш код для входа по Сбер ID в Okko. Никому его не сообщайт"
        encrypted = "uFcPfFL7BmiNi72EDCFtUuloUL59OC4++dYwilfqLGfQ7Dw5/pYpalJvlCp12CwVBHkUKjkxqwFyIGTjdPyFCpjwG9V6gvHNhNxio/xt07CYM4uD4rqqaYqFWf+Esc0XYmuatKPrwINbvN1ryWS4ddHqhki9uFtmRzFl7pfuzxx9Zdu8SbBrlmSaK1vR2cQ0s6A/rwpQ2rs7YRs9GAim0pKbGLC5q97SajLwsLOv2d92OwXYIvyJFawRkUU0fg=="
        decrypted = self.cipher.decrypt(encrypted)
        self.assertEqual(original_text, decrypted)

    def test_real_value(self):
        # UnicodeDecodeError: 'utf-8' codec can't decode byte 0x8e in position 0: invalid start byte
        original_text = """SMS
SMS from: 1068055500021229
Received on SIM: 1
【拼多多】您正在登录拼多多，验证码是828627。请于5分钟内完成验证，若非本人操作，请忽略本短信。"""
        cipher = AES256Cipher(
            dotenv.get("AUTH_KEY")
        )
        baseencoded_body_from_frontend = "NE8P9oXSyWu+dri/QykyZtZr2I4ZXUF0xmaTKuWmiHHVdS7C7wTaQMJZUyXSLEIyRLyX7sBTMH8QN8CmHmEpIgLbA70fFFdgkLSZ7UVAP6/3bMPObKsDXzONsi/QVCeNrXbK1Yfpwn4eWafCoKA5KUh3aPwUVcVEctVdIoDF+izMwwlEj9626NavJtlYR8cg4xfSecqYiEPJCAH4DlFnSBn+PYycWJddrnVmHHM1QSB9nEtgvlQ8PF6fIDm7m4I5dnpRBbWUTjQxdARG6LmB52+UvTpJESkEhMwyFxDa3p9BYvkJP6E="
        decrypted = cipher.decrypt(baseencoded_body_from_frontend)
        self.assertEqual(original_text, decrypted)


if __name__ == "__main__":
    unittest.main()
