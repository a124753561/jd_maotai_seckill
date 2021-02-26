import sys
from tmall_spider_requests import TmallSeckill

if __name__ == '__main__':
    a = """

        ooooooooooo oooo     oooo          oooooooo8                        oooo        o88   o888  o888  
        88  888  88  8888o   888          888          ooooooooo8  ooooooo   888  ooooo oooo   888   888  
            888      88 888o8 88 ooooooooo 888oooooo  888oooooo8 888     888 888o888     888   888   888  
            888      88  888  88                  888 888        888         8888 88o    888   888   888  
           o888o    o88o  8  o88o         o88oooo888    88oooo888  88ooo888 o888o o888o o888o o888o o888o                                                                                                                                                  
                                               
功能列表：                                                                                
 1.预约商品
 2.秒杀抢购商品
    """
    print(a)

    tmall_seckill = TmallSeckill()
    choice_function = input('请选择:')
    if choice_function == '1':
        tmall_seckill.reserve()
    elif choice_function == '2':
        tmall_seckill.seckill_by_proc_pool()
    else:
        print('没有此功能')
        sys.exit(1)
