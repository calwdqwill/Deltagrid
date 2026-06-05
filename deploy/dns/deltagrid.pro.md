# DNS для `deltagrid.pro`

Текущий целевой сервер для деплоя DeltaGrid:

```text
2.25.143.143
```

## Что выставить в панели домена

Для apex-домена:

```text
Type: A
Name: @
Value: 2.25.143.143
TTL: 300 или 3600
```

Для `www`:

```text
Type: CNAME
Name: www
Value: deltagrid.pro
TTL: 300 или 3600
```

Либо вместо `CNAME` можно использовать:

```text
Type: A
Name: www
Value: 2.25.143.143
TTL: 300 или 3600
```

## IPv6

Сейчас у домена есть AAAA-запись на REG.RU:

```text
2a00:f940:2:2:1:1:0:266
```

Если у нового сервера нет настроенного IPv6, удалите AAAA-записи для `@` и `www`, иначе часть пользователей может попадать на старый хостинг или видеть ошибку.

## Проверка

```bash
dig +short deltagrid.pro A
dig +short www.deltagrid.pro A
dig +short deltagrid.pro AAAA
```

Ожидаемо:

```text
deltagrid.pro A -> 2.25.143.143
www.deltagrid.pro -> CNAME deltagrid.pro или A 2.25.143.143
AAAA -> пусто, если IPv6 не используется
```

SSL через Let's Encrypt запускайте только после того, как публичная проверка DNS показывает `2.25.143.143`. Если A-запись ещё указывает на `31.31.196.50` или AAAA ведёт на старый REG.RU hosting, Certbot выпустит сертификат не для того сервера или завершится ошибкой.
