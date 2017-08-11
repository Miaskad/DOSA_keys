from django.shortcuts import render, HttpResponseRedirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db.models import Sum

import time
import serial
import string
from datetime import datetime
from decimal import Decimal

from .models import KeyOwner, Database, Cistern, Connect, Licenced


from pytz import timezone
from dateutil.relativedelta import relativedelta


kiev = timezone('Europe/Kiev')

dev = serial.Serial()
dev.timeout = 1


# Доступные порты
def scan():
    available = []
    for i in range(256):
        try:
            s = serial.Serial(i)
            available.append(s.portstr)
            s.close()
        except serial.SerialException:
            pass
    return available


def ready(request):
    if Licenced.objects.exists():
        if not Licenced.objects.all()[0].trial:
            return True
        elif Licenced.objects.all()[0].date_time > datetime.today().date():
            return True
        else:
            if request.user.is_superuser:
                messages.add_message(request, messages.ERROR, 'Срок лицензии истек. Введите ключ')
            else:
                messages.add_message(request, messages.ERROR, 'Срок лицензии истек. Обратитесь к администратору')
            return False
    else:
        dt = datetime.today().date() + relativedelta(months=1)
        Licenced.objects.create(date_time=dt)
        return True


# Создание порта
@user_passes_test(lambda u: u.is_superuser)
def com_settings(request):
    if not ready(request):
        return HttpResponseRedirect('/licence/')
    av_ports = tuple(scan())
    if not av_ports:
        messages.add_message(request, messages.ERROR, 'Нет доступных устройств.')
        return HttpResponseRedirect('/admin/')
    try:
        conn = Connect.objects.first()
    except Connect.DoesNotExist:
        conn = None
    if request.method == 'POST':
        connect, created = Connect.objects.update_or_create(port__icontains='COM',
                                                            defaults={'port': request.POST.get('port'),
                                                                      'speed': int(request.POST.get('speed'))})
    return render(request, 'loads/settings.html', {'cur_user': request.user.username, 'ports': av_ports, 'conn': conn})


# Чтение БД ключей с устройства
def read_keys():
    for ent in range(len('view keys\r')):
        dev.write('view keys\r'[ent].encode())
    insert_text = dev.readline()
    text = insert_text.decode('utf-8')
    while 'DOSA-10W>' not in text:
        insert_text += dev.readline()
        text = insert_text.decode()
    text = text[0:-10]
    text = text.replace('\r', ' ')
    text = text.replace('\t', ' ')
    text = text.replace('\n', ' ')

    a = text.split(' ')
    temp_mas = []
    for i in range(len(a)):
        if a[i] != '':
            temp_mas.append(a[i])
    temp_mas = temp_mas[:-6]
    num_el = int((len(temp_mas)))
    num_str = int(num_el/2)
    key_mas = []
    for i in range(num_str):
        key_mas.append([])
        for j in range(2):
            key_mas[i].append(temp_mas[i*2+j])
    for i in range(num_str):
        if key_mas[i][1] == 'FFFFFFFFFFFFFFFF':
            break
        KeyOwner.objects.get_or_create(keys=key_mas[i][1])


# Чтение БД отгрузок с устройства
def read_log():
    for ent in range(len('view log\r')):
        dev.write('view log\r'[ent].encode())
    insert_text = dev.readline()
    text = insert_text.decode('utf-8')
    while 'DOSA-10W>' not in text:
        insert_text += dev.readline()
        text = insert_text.decode()
    text = text[0:-10]
    text = text.replace('\r', ' ')
    text = text.replace('\t', ' ')
    text = text.replace('\n', ' ')
    a = text.split(' ')

    temp_mas = []
    for i in range(len(a)):
        if a[i] != '':
            temp_mas.append(a[i])
    temp_mas = temp_mas[9:]
    num_el = int((len(temp_mas)))
    num_str = int(num_el/8)
    mas = []
    for i in range(num_str):
        mas.append([])
        for j in range(8):
            mas[i].append(temp_mas[i*8+j])
    for i in range(num_str):
        us, created = KeyOwner.objects.get_or_create(keys=mas[i][1])
        devout, created = Database.objects.get_or_create(op_id=mas[i][0],
                                                         dosed=Decimal(mas[i][2]),
                                                         date_time=kiev.localize(datetime.strptime(mas[i][4]+' '+mas[i][5],
                                                                                                   "%d.%m.%Y %H:%M")),
                                                         user=us)
        if created:
            if us.cistern:
                # Recalculate cistern volumes
                previous = Database.objects.filter(user__cistern=us.cistern,
                                                   date_time__lt=devout.date_time).order_by('-date_time')
                if len(previous) > 0:
                    previous_cist_volume = previous[0].cistern_volume
                else:
                    previous_cist_volume = us.cistern.start_volume
                devout.cistern_volume = previous_cist_volume - devout.dosed + devout.add
                next_cist_dosings = Database.objects.filter(user__cistern=us.cistern,
                                                            date_time__gt=devout.date_time).order_by('date_time')
                if len(next_cist_dosings):
                    previous_cist_volume = devout.cistern_volume
                    for load in next_cist_dosings:
                        load.cistern_volume = previous_cist_volume - load.dosed + load.add
                        previous_cist_volume = load.cistern_volume
                        load.save()
                # Recalculate fuel volumes
                by_fuel = Database.objects.filter(date_time__lt=devout.date_time,
                                                  user__cistern__fuel=us.cistern.fuel).order_by('-date_time')
                if len(by_fuel) > 0:
                    previous_fuel_volume = by_fuel[0].fuel_volume
                else:
                    fuel_cists = Cistern.objects.filter(fuel=us.cistern.fuel)
                    previous_fuel_volume = fuel_cists.aggregate(Sum('start_volume'))['start_volume__sum']
                devout.fuel_volume = previous_fuel_volume - devout.dosed + devout.add
                devout.save()
                next_dosings = Database.objects.filter(date_time__gt=devout.date_time,
                                                       user__cistern__fuel=us.cistern.fuel).order_by('date_time')
                if len(next_dosings):
                    previous_fuel_volume = devout.fuel_volume
                    for load in next_dosings:
                        load.fuel_volume = previous_fuel_volume - load.dosed + load.add
                        previous_fuel_volume = load.fuel_volume
                        load.save()


def recalc(request, cist, fuels):
    cist_db = Database.objects.filter(user__cistern=cist).order_by('date_time')
    if len(cist_db):
        cist_db[0].cistern_volume = cist.start_volume - cist_db[0].dosed + cist_db[0].add
        cist_db[0].save()
        cur_cist_volume = cist_db[0].cistern_volume
        for cist_load in cist_db[1:]:
            cist_load.cistern_volume = cur_cist_volume - cist_load.dosed + cist_load.add
            cur_cist_volume = cist_load.cistern_volume
            cist_load.save()
    for f in fuels:
        fuel_db = Database.objects.filter(user__cistern__fuel=f).order_by('date_time')
        if len(fuel_db):
            fuel_vol = Cistern.objects.filter(fuel=f).aggregate(Sum('start_volume'))['start_volume__sum']
            fuel_db[0].fuel_volume = fuel_vol - fuel_db[0].dosed + fuel_db[0].add
            fuel_db[0].save()
            fuel_vol = fuel_db[0].fuel_volume
            for fuel_load in fuel_db[1:]:
                fuel_load.fuel_volume = fuel_vol - fuel_load.dosed + fuel_load.add
                fuel_vol = fuel_load.fuel_volume
                fuel_load.save()


# Обновление БД ключей
def refr_keys(request):
    conn = Connect.objects.first()
    if conn == None:
        if request.user.is_superuser:
            messages.add_message(request, messages.ERROR, 'Задайте параметры подключения.')
            return HttpResponseRedirect('/admin/settings/')
        else:
            messages.add_message(request, messages.ERROR, 'Не заданы параметры подключения. Обратитесь к администратору')
            return HttpResponseRedirect('/user/keys/')
    dev.port = conn.port
    dev.baudrate = conn.speed
    if not dev.isOpen():
        try:
            dev.open()
        except OSError:
            messages.add_message(request, messages.ERROR,
                                 'Невозможно установить соединение c ' + dev.port +
                                 '. Проверьте подключение устройства к компьютеру')
            if request.user.is_superuser:
                return HttpResponseRedirect('/admin/keys/')
            else:
                return HttpResponseRedirect('/user/keys/')
        repeat = 0
        while repeat < 2:
            for log_on in range(len('clion\r')):
                dev.write('clion\r'[log_on].encode())
            resp = dev.readline()
            if 'DOSA-10W' in resp.decode():
                read_keys()
                for log_off in range(len('clioff\r')):
                    dev.write('clioff\r'[log_off].encode())
                dev.readline()
                dev.close()
                repeat = 2
            else:
                time.sleep(2)
                repeat += 1
                if repeat == 2:
                    dev.close()
                    messages.add_message(request, messages.ERROR, 'Обмен данными c ' + dev.port +
                                         ' невозможен. Проверьте соединение устройства с RS и выполните подключение')
                    if request.user.is_superuser:
                        return HttpResponseRedirect('/admin/keys/')
                    else:
                        return HttpResponseRedirect('/user/keys/')
    if request.user.is_superuser:
        return HttpResponseRedirect('/admin/keys/')
    else:
        return HttpResponseRedirect('/user/keys/')


# Обновление БД отгрузок
def refr_loads(request):
    if not Cistern.objects.exists():
        if request.user.is_superuser:
            if not KeyOwner.objects.exists():
                messages.add_message(request, messages.ERROR, 'Считайте перечень ключей с устройства и '
                                                              'задайте параметры резервуара для продолжения работы')
                return HttpResponseRedirect('/admin/keys/')
            else:
                messages.add_message(request, messages.ERROR, 'Задайте параметры резервуара для продолжения работы')
                return HttpResponseRedirect('/admin/cisterns/add-cistern/')
        else:
            messages.add_message(request, messages.ERROR, 'В системе нет зарегистрированных резервуаров. '
                                                          'Обратитесь к администратору')
            return HttpResponseRedirect('/user/')
    if KeyOwner.objects.filter(cistern=None).exists():
        messages.add_message(request, messages.WARNING, 'Не все ключи привязаны к резервуарам. При считывании отгрузок '
                                                        'по данным ключам рассчет объема производится не будет')
    conn = Connect.objects.first()
    if conn == None:
        if request.user.is_superuser:
            messages.add_message(request, messages.ERROR, 'Задайте параметры подключения.')
            return HttpResponseRedirect('/admin/settings/')
        else:
            messages.add_message(request, messages.ERROR, 'Не заданы параметры подключения. Обратитесь к администратору')
            return HttpResponseRedirect('/user/')
    dev.port = conn.port
    dev.baudrate = conn.speed
    if not dev.isOpen():
        try:
            dev.open()
        except OSError:
            messages.add_message(request, messages.ERROR,
                                 'Невозможно установить соединение c ' + dev.port +
                                 '. Проверьте подключение устройства к компьютеру')
            if request.user.is_superuser:
                return HttpResponseRedirect('/admin/')
            else:
                return HttpResponseRedirect('/user/')
        repeat = 0
        while repeat < 2:
            for log_on in range(len('clion\r')):
                dev.write('clion\r'[log_on].encode())
            resp = dev.readline()
            if 'DOSA-10W' in resp.decode():
                read_log()
                for log_off in range(len('clioff\r')):
                    dev.write('clioff\r'[log_off].encode())
                dev.readline()
                dev.close()
                repeat = 2
            else:
                time.sleep(2)
                repeat += 1
                if repeat == 2:
                    dev.close()
                    messages.add_message(request, messages.ERROR, 'Обмен данными c ' + dev.port +
                                         ' невозможен. Проверьте соединение устройства с RS и выполните подключение')
                    if request.user.is_superuser:
                        return HttpResponseRedirect('/admin/')
                    else:
                        return HttpResponseRedirect('/user/')
    if request.user.is_superuser:
        return HttpResponseRedirect('/admin/')
    else:
        return HttpResponseRedirect('/user/')


# Добавление ключей
def add_key(request, key_doc):
    conn = Connect.objects.first()
    if conn == None:
        messages.add_message(request, messages.ERROR, 'Задайте параметры подключения.')
        return HttpResponseRedirect('/admin/settings/')
    dev.port = conn.port
    dev.baudrate = conn.speed
    if not dev.isOpen():
        try:
            dev.open()
        except OSError:
            messages.add_message(request, messages.ERROR,
                                 'Невозможно установить соединение c ' + dev.port +
                                 '. Проверьте подключение устройства к компьютеру')
            return HttpResponseRedirect('/admin/')
        repeat = 0
        while repeat < 2:
            for log_on in range(len('clion\r')):
                dev.write('clion\r'[log_on].encode())
            resp = dev.readline()
            if 'DOSA-10W' in resp.decode():
                for ByteIn in range(len('import keys\r')):
                    dev.write('import keys\r'[ByteIn].encode())
                dev.readline()
                for key in key_doc:
                    if len(key) == 16 and all(c in string.hexdigits for c in key):
                        dev.write('\n'.encode())
                        for KeyByte in range(len(key)):
                            dev.write((key[KeyByte]).encode())
                stop = 'DOSA-10W>'
                insert_text = dev.readline()
                text = insert_text.decode()
                while stop not in text:
                    insert_text += dev.readline()
                    text = insert_text.decode('utf-8')
                read_keys()
                for key_off in range(len('clioff\r')):
                        dev.write('clioff\r'[key_off].encode())
                dev.readline()
                dev.close()
                repeat = 2
            else:
                time.sleep(2)
                repeat += 1
                if repeat == 2:
                    dev.close()
                    messages.add_message(request, messages.ERROR, 'Обмен данными c ' + dev.port +
                                         ' невозможен. Проверьте соединение устройства с RS и выполните подключение')
                    return HttpResponseRedirect('/admin/keys/')
    return HttpResponseRedirect('/admin/keys/')