import requests
from flask import current_app

class ExternalAPIService:
    @staticmethod
    def _headers():
        return {
            'Authorization': f"Bearer {current_app.config['EXTERNAL_API_KEY']}",
            'Content-Type': 'application/json'
        }

    @classmethod
    def _base(cls):
        return current_app.config['EXTERNAL_API_URL']

    @classmethod
    def lay_danh_sach_giang_vien(cls):
        try:
            r = requests.get(f"{cls._base()}/api/giang-vien", headers=cls._headers(), timeout=5)
            return r.json() if r.status_code == 200 else None
        except Exception as e:
            current_app.logger.error(f'[API] lay_giang_vien: {e}')
            return None

    @classmethod
    def gui_thong_bao_phan_cong(cls, email, ten_mon, ten_don_vi):
        try:
            data = {'email': email,
                    'tieu_de': f'Phân công hiệu chỉnh: {ten_mon}',
                    'noi_dung': f'Bạn được mời hiệu chỉnh đề cương môn {ten_mon} - {ten_don_vi}'}
            r = requests.post(f"{cls._base()}/api/thong-bao", json=data, headers=cls._headers(), timeout=5)
            return r.status_code == 200
        except Exception as e:
            current_app.logger.error(f'[API] gui_thong_bao: {e}')
            return False
