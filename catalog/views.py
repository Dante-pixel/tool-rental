import re
import urllib.parse
import hashlib
import requests
import xml.etree.ElementTree as ET
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Tool, Category, ToolVariant, RentalTariff, Order, OrderItem

# Настройки Freedom Pay. На проде настоятельно рекомендуется вынести в .env!
MERCHANT_ID = 'ТВОЙ_ID_МЕРЧАНТА_ИЗ_ЛИЧНОГО_КАБИНЕТА'
SECRET_KEY = 'ТВОЙ_СЕКРЕТНЫЙ_КЛЮЧ_ИЗ_ЛИЧНОГО_КАБИНЕТА'


def generate_signature(script_name, params, secret_key):
    """Генерирует обязательную цифровую подпись pg_sig для Freedom Pay"""
    params_to_sign = {k: v for k, v in params.items() if k != 'pg_sig'}
    sorted_keys = sorted(params_to_sign.keys())
    values_list = [str(params_to_sign[k]) for k in sorted_keys]
    sign_string = f"{script_name};{';'.join(values_list)};{secret_key}"
    return hashlib.md5(sign_string.encode('utf-8')).hexdigest()


def index(request):
    cat_id = request.GET.get('category')
    sub_id = request.GET.get('subcategory')
    tools = Tool.objects.all()
    if sub_id:
        tools = tools.filter(subcategory_id=sub_id)
    elif cat_id:
        tools = tools.filter(category_id=cat_id)
    categories = Category.objects.prefetch_related('subcategories').all()
    return render(request, 'catalog/index.html', {
        'tools': tools,
        'categories': categories,
        'current_category': int(cat_id) if cat_id else None
    })


def tool_detail(request, pk):
    tool = get_object_or_404(Tool.objects.prefetch_related('images', 'tariffs', 'variants'), pk=pk)
    return render(request, 'catalog/tool_detail.html', {'tool': tool})


def add_to_cart(request, tool_id):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        quantity = int(request.POST.get('quantity', 1))
        variant_id = request.POST.get('variant_id')
        tariff_id = request.POST.get('tariff_id')
        tool = get_object_or_404(Tool, id=tool_id)

        size_name = "Стандарт"
        price_val = "0"

        if tariff_id and tariff_id != "base" and tariff_id != "":
            tariff = get_object_or_404(RentalTariff, id=tariff_id)
            price_val = str(tariff.price)
            size_name = tariff.time_period
            item_key = f"{tool_id}_tariff_{tariff_id}"
        elif variant_id and variant_id != "base" and variant_id != "":
            variant = get_object_or_404(ToolVariant, id=variant_id)
            price_val = str(variant.price)
            size_name = variant.size_name
            item_key = f"{tool_id}_var_{variant_id}"
        else:
            price_val = str(tool.price_per_day)
            item_key = f"{tool_id}_base"

        price_digits = re.sub(r'\D', '', str(price_val))
        clean_price = int(price_digits) if price_digits else 0

        if item_key in cart:
            cart[item_key]['quantity'] += quantity
        else:
            cart[item_key] = {
                'title': tool.title,
                'price': clean_price,
                'size': size_name,
                'quantity': quantity,
                'image': tool.image.url if tool.image else ''
            }

        request.session['cart'] = cart
        request.session.modified = True
        return redirect('cart_detail')


def cart_detail(request):
    cart = request.session.get('cart', {})
    total_price = sum(item['price'] * item['quantity'] for item in cart.values())

    if request.method == 'POST' and cart:
        # 1. Создаем объект заказа в базе данных
        order = Order.objects.create(
            customer_name=request.POST.get('customer_name'),
            customer_phone=request.POST.get('customer_phone'),
            total_price=total_price,
            status='new'
        )

        # 2. Переносим товары из корзины сессии в базу OrderItem
        for item_key, data in cart.items():
            OrderItem.objects.create(
                order=order,
                title=data['title'],
                size=data['size'],
                price=data['price'],
                quantity=data['quantity']
            )

        payment_method = request.POST.get('payment_method', 'whatsapp')

        if payment_method == 'visa':
            # --- СЦЕНАРИЙ А: ОНЛАЙН ОПЛАТА КАРТОЙ (FREEDOM PAY) ---
            script_name = "init_payment.php"
            url = f"https://api.freedompay.money/{script_name}"

            # Очищаем корзину сессии ПЕРЕД переходом на страницу успеха
            request.session['cart'] = {}
            request.session.modified = True

            # Формируем параметры инициации транзакции (для будущего использования)
            params = {
                'pg_merchant_id': MERCHANT_ID,
                'pg_order_id': str(order.id),
                'pg_amount': str(int(order.total_price)),
                'pg_currency': 'KGS',
                'pg_description': f"Аренда строительного инструмента по заказу №{order.id}",
                'pg_salt': f"salt_order_{order.id}_secure",
                'pg_success_url': 'https://vanilla-corny-unnerve.ngrok-free.dev/payment/success/',
                'pg_failure_url': 'https://vanilla-corny-unnerve.ngrok-free.dev/payment/failure/',
            }
            params['pg_sig'] = generate_signature(script_name, params, SECRET_KEY)

            try:
                # ВРЕМЕННЫЙ ТЕСТ: Эмулируем успешный ответ платежки без отправки запроса наружу
                order.is_paid = True
                order.status = 'paid'  # Будет отображаться в админке
                order.save()

                # Перенаправляем на страницу успешной оплаты
                return redirect('payment_success')

            except Exception as e:
                return render(request, 'catalog/cart_detail.html', {
                    'cart': cart, 'total_price': total_price,
                    'error': f"Ошибка сохранения заказа: {str(e)}"
                })

        else:
            # --- СЦЕНАРИЙ Б: СТАНДАРТНОЕ ОФОРМЛЕНИЕ В WHATSAPP ---
            whatsapp_text = f"Здравствуйте! Оформил заказ на сайте PROKAT-INSTRUMENT.KG\n\nЗаказ №{order.id}\nИмя: {order.customer_name}\nТелефон: {order.customer_phone}\nИтоговая сумма: {order.total_price} сом\n\nНаш менеджер свяжется с вами."
            whatsapp_url = f"https://wa.me/996702747714?text={urllib.parse.quote(whatsapp_text)}"

            request.session['cart'] = {}
            return redirect(whatsapp_url)

    return render(request, 'catalog/cart_detail.html', {'cart': cart, 'total_price': total_price})


@csrf_exempt
def freedom_pay_result(request):
    """Фоновый Result URL для Freedom Pay"""
    if request.method != 'POST':
        return HttpResponse("Method not allowed", status=405)

    data = request.POST.dict()
    if 'pg_sig' not in data:
        return HttpResponse("Missing signature", status=400)

    incoming_sig = data['pg_sig']
    calculated_sig = generate_signature('result', data, SECRET_KEY)

    if incoming_sig != calculated_sig:
        return HttpResponse("Invalid signature", status=400)

    order_id = data.get('pg_order_id')
    payment_status = data.get('pg_result')  # '1' — успех, '0' — отказ

    order = get_object_or_404(Order, id=order_id)

    response_params = {
        'pg_merchant_id': MERCHANT_ID,
        'pg_status': 'ok',
        'pg_salt': data.get('pg_salt', 'salt'),
    }

    if payment_status == '1':
        order.is_paid = True
        order.status = 'paid'
        order.save()
        response_params['pg_description'] = "Платеж успешно обработан сайтом"
    else:
        order.status = 'failed'
        order.save()
        response_params['pg_description'] = "Фиксация отмены или неуспешного платежа"

    response_params['pg_sig'] = generate_signature('result', response_params, SECRET_KEY)

    xml_response = f"""<?xml version="1.0" encoding="utf-8"?>
    <response>
        <pg_merchant_id>{response_params['pg_merchant_id']}</pg_merchant_id>
        <pg_status>{response_params['pg_status']}</pg_status>
        <pg_description>{response_params['pg_description']}</pg_description>
        <pg_salt>{response_params['pg_salt']}</pg_salt>
        <pg_sig>{response_params['pg_sig']}</pg_sig>
    </response>"""

    return HttpResponse(xml_response, content_type="text/xml")


def clear_cart(request):
    if 'cart' in request.session:
        del request.session['cart']
    return redirect('index')


def search(request):
    query = request.GET.get('q', '').strip()
    results = Tool.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query)
    ).distinct() if query else Tool.objects.none()
    return render(request, 'catalog/search_results.html', {'query': query, 'tools': results})


def conditions_page(request):
    return render(request, 'catalog/conditions.html')


def contacts_page(request):
    return render(request, 'catalog/contacts.html')


def payment_success(request):
    return render(request, 'catalog/payment_success.html')


def payment_failure(request):
    return render(request, 'catalog/payment_failure.html')