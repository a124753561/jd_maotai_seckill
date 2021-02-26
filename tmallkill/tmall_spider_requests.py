# coding=utf-8
# !/usr/bin/python
import functools
import requests
from concurrent.futures import ProcessPoolExecutor
from tmall_logger import logger
from config import global_config
from exception import SKException


class SpiderSession:
    def __init__(self):
        self.cookies_dir_path = "./cookies/"
        self.user_agent = global_config.getRaw('config', 'DEFAULT_USER_AGENT')
        self.session = self._init_session()

    def get_session(self):
        """
        获取当前Session
        :return:
        """
        return self.session

    def _init_session(self):
        session = requests.session()
        # 关闭多余的链接
        session.keep_alive = False
        session.headers = self.get_headers()
        return session

    def get_headers(self):
        return {"User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;"
                          "q=0.9,image/avif,image/webp,image/apng,*/*;"
                          "q=0.8,application/signed-exchange;"
                          "v=b3;"
                          "q=0.9",
                "Connection": "keep-alive"}


class QrLogin:
    """
    扫码登录
    """

    def __init__(self, spider_session: SpiderSession):
        """
        初始化扫码登录
        大致流程：
            1、访问登录二维码页面，获取Token
            2、使用Token获取票据
            3、校验票据
        :param spider_session:
        """
        self.qrcode_img_file = 'qr_code.png'

        self.spider_session = spider_session
        self.session = self.spider_session.get_session()

        self.is_login = False
        self.refresh_login_status()

    def refresh_login_status(self):
        """
        刷新是否登录状态
        :return:
        """
        self.is_login = self._validate_cookies()

    def _validate_cookies(self):
        """
       验证cookies是否有效（是否登陆）
       通过访问用户订单列表页进行判断：若未登录，将会重定向到登陆页面。
       :return: cookies是否有效 True/False
       """
        url = 'https://i.taobao.com/my_taobao.htm'
        payload = {
            "spm": "0.0.0.0.sHoUVp"
        }
        try:
            resp = self.session.get(url=url, params=payload, allow_redirects=False)
            if resp.status_code == requests.codes.OK:
                return True
        except Exception as e:
            logger.error("验证cookies是否有效发生异常", e)
        return False

    def _get_qrcode(self):
        """
        缓存并展示登录二维码
        :return:
        """
        url = 'https://login.taobao.com/newlogin/qrcode/generate.do?appName=taobao&fromSite=0&sub=true&allp=assets_css%3D3.0.10%2Flogin_pc.css&appName=taobao&appEntrance=tmall&_csrf_token=FUM89ttUvVLJZBaBYSeRJ8&umidToken=d7528777ecdf31ada1405b253d3ddc5d3f9455e2&hsiz=16fe6d9c18f88635a2cf247060ed2cdf&newMini2=true&bizParams=&full_redirect=true&style=miniall&appkey=00000000&from=tmall&isMobile=false&lang=zh_CN&returnUrl=https:%2F%2Fwww.tmall.com&fromSite=0'
        payload = {
            'appid': 133,
            'size': 147,
            't': str(int(time.time() * 1000)),
        }
        headers = {
            'User-Agent': self.spider_session.get_user_agent(),
            'Referer': 'https://passport.jd.com/new/login.aspx',
        }
        resp = self.session.get(url=url, headers=headers, params=payload)

        if not response_status(resp):
            logger.info('获取二维码失败')
            return False

        save_image(resp, self.qrcode_img_file)
        logger.info('二维码获取成功，请打开京东APP扫描')
        open_image(self.qrcode_img_file)
        return True
    def _get_login_page(self):
        """
        获取PC端登录页面
        :return:
        """
        url = "https://login.tmall.com/"
        page = self.session.get(url, headers=self.spider_session.get_headers())
        return page

    def login_by_qrcode(self):
        """
        二维码登陆
        :return:
        """
        self._get_login_page()

        # download QR code
        if not self._get_qrcode():
            raise SKException('二维码下载失败')

        # get QR code ticket
        ticket = None
        retry_times = 85
        for _ in range(retry_times):
            ticket = self._get_qrcode_ticket()
            if ticket:
                break
            time.sleep(2)
        else:
            raise SKException('二维码过期，请重新获取扫描')

        # validate QR code ticket
        if not self._validate_qrcode_ticket(ticket):
            raise SKException('二维码信息校验失败')

        self.refresh_login_status()

        logger.info('二维码登录成功')


class TmallSeckill(object):
    def __init__(self):
        self.spider_session = SpiderSession()
        self.qrlogin = QrLogin(self.spider_session)

    def check_login(func):
        """
        用户登陆态校验装饰器。若用户未登陆，则调用扫码登陆
        """

        @functools.wraps(func)
        def new_func(self, *args, **kwargs):
            if not self.qrlogin.is_login:
                logger.info("{0} 需登陆后调用，开始扫码登陆".format(func.__name__))
                self.login_by_qrcode()
            return func(self, *args, **kwargs)

        return new_func
    def login_by_qrcode(self):
        """
        二维码登陆
        :return:
        """
        if self.qrlogin.is_login:
            logger.info('登录成功')
            return

        self.qrlogin.login_by_qrcode()

        if self.qrlogin.is_login:
            self.nick_name = self.get_username()
            self.spider_session.save_cookies_to_local(self.nick_name)
        else:
            raise SKException("二维码登录失败！")

    def seckill_by_proc_pool(self, work_count=5):
        """
        多进程进行抢购
        work_count：进程数量
        """
        with ProcessPoolExecutor(work_count) as pool:
            for i in range(work_count):
                pool.submit(self.seckill)

    @check_login
    def seckill(self):
        """
        抢购
        """
        self._seckill()

    def _seckill(self):
        pass
