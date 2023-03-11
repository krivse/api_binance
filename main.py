import logging
from binance import ThreadedWebsocketManager
from binance.exceptions import BinanceAPIException


SYMBOL = ['ETH/USDT']


class Binance:
    SOCKET = None
    BM = ThreadedWebsocketManager()

    def __init__(self, symbol: list):
        self.symbol = symbol[0]
        self.BM.start()
        self.start()

    def start(self):
        """Запуск программы на получение пары."""
        try:
            self.SOCKET = self.BM.start_symbol_ticker_futures_socket(
                callback=self._socket_message_start, symbol='ETHUSDT'
            )
        except BinanceAPIException as err:
            logging.error(f'Несуществующее название пары: {err}')

    def _socket_message_start(self, msg):
        """Устанавливаем фиксированные первоначальное значение time и price."""
        if 'data' in msg:
            start_price = msg.get('data', 'Нет ключа "data"').get('b', 'Нет ключа "b"')
            start_time = msg.get('data', 'Нет ключа "data"').get('T', 'Нет ключа "T"') / 1000
            self._socket_message_next(start_price, start_time, msg)
        else:
            logging.error(f'Error: {msg["m"]}')
            self.reset_socket()

    def _socket_message_next(self, start_price, start_time, msg):
        """
        В течении часа от start_time будет рассчитываться максимальное отклонение в цене
       Если текущая цена current_price отличается от начальной цены start_price на 1%,
       то будет выводится сообщение в консоль.
       """
        if 'data' in msg:
            current_price = msg.get('data', 'Нет ключа "data"').get('b', 'Нет ключа "b"')
            time_event = msg.get('data', 'Нет ключа "data"').get('T', 'Нет ключа "T"') / 1000
            percent = (float(current_price) - float(start_price)) / float(start_price) * 100
            if time_event - start_time < 3600 and (percent >= 1 or percent <= -1):
                print(f'Цена изменена более чем на 1% и составляет: {current_price}. '
                      f'Процентое соотношение между начальной и текущей ценой: {percent} %')
            else:
                start_time = time_event
                start_price = current_price
        else:
            logging.error(f'Error: {msg["m"]}')
            self.reset_socket()

    def reset_socket(self):
        """Перезапуск после ошибки."""
        self.BM.stop_socket(self.SOCKET)
        self.start()

    def join(self):
        self.BM.join()


if __name__ == "__main__":
    try:
        start = Binance(SYMBOL)
        start.join()
        logging.info('start polling')
    except (KeyboardInterrupt, SystemExit):
        logging.info('stop polling')
