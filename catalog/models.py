from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Категория")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories',
                                 verbose_name="Категория")
    name = models.CharField(max_length=100, verbose_name="Название подкатегории")

    def __str__(self):
        return f"{self.category.name} -> {self.name}"

    class Meta:
        verbose_name = "Подкатегория"
        verbose_name_plural = "Подкатегории"


class Tool(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория")
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name="Подкатегория")
    title = models.CharField(max_length=200, verbose_name="Название товара/инструмента")
    description = models.TextField(verbose_name="Описание", blank=True, null=True)
    price_per_day = models.CharField(max_length=50, verbose_name="Цена в сутки (базовая)", blank=True, null=True)
    deposit = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Залог")
    image = models.ImageField(upload_to='tools/', verbose_name="Главное фото")
    is_available = models.BooleanField(default=True, verbose_name="Доступно сейчас")
    full_description = models.TextField(verbose_name="Полное описание", blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Все товары (Инструменты)"


# 1. БЛОК: ГАЛЕРЕЯ
class ToolImage(models.Model):
    tool = models.ForeignKey(Tool, on_delete=models.CASCADE, related_name='images', verbose_name="Товар")
    image = models.ImageField(upload_to='tools/gallery/', verbose_name="Дополнительное фото")

    class Meta:
        verbose_name = "Дополнительное фото"
        verbose_name_plural = "ГАЛЕРЕЯ ФОТОГРАФИЙ"


# 2. БЛОК: ФИЗИЧЕСКИЕ РАЗМЕРЫ / ДИАМЕТРЫ
class ToolVariant(models.Model):
    tool = models.ForeignKey(Tool, on_delete=models.CASCADE, related_name='variants', verbose_name="Товар")
    size_name = models.CharField(max_length=100, verbose_name="РАЗМЕР / ДИАМЕТР")
    # ИСПРАВЛЕНО: Изменили на price (целое число), чтобы корзина работала корректно
    price = models.PositiveIntegerField(verbose_name="ЦЕНА ЗА ЭТОТ РАЗМЕР", default=0)
    variant_image = models.ImageField(upload_to='variants/', null=True, blank=True, verbose_name="ФОТО ЭТОГО РАЗМЕРА")

    class Meta:
        verbose_name = "Вариант размера"
        verbose_name_plural = "ВАРИАНТЫ ФИЗИЧЕСКИХ РАЗМЕРОВ"


# 3. БЛОК: ТАРИФЫ ВРЕМЕНИ
class RentalTariff(models.Model):
    tool = models.ForeignKey(Tool, on_delete=models.CASCADE, related_name='tariffs', verbose_name="Товар")
    time_period = models.CharField(max_length=100, verbose_name="СРОК АРЕНДЫ (Час/Сутки/День)")
    price = models.CharField(max_length=100, verbose_name="ЦЕНА ЗА СРОК")

    class Meta:
        verbose_name = "Тариф аренды"
        verbose_name_plural = "ТАРИФЫ И СРОКИ АРЕНДЫ"


# 4. БЛОК: КОЛИЧЕСТВО ТОВАРА В НАЛИЧИИ
class ToolQuantity(models.Model):
    tool = models.ForeignKey(Tool, on_delete=models.CASCADE, related_name='quantities', verbose_name="Товар")
    count = models.PositiveIntegerField(default=1, verbose_name="Количество")

    class Meta:
        verbose_name = "Количество"
        verbose_name_plural = "КОЛИЧЕСТВО ТОВАРА"


# --- НОВЫЙ БЛОК 5: СИСТЕМА ЗАКАЗОВ (ДЛЯ БАЗЫ И ПОД ПЛАТЕЖИ) ---

from django.db import models


class Order(models.Model):
    customer_name = models.CharField(max_length=100, verbose_name="Имя клиента")
    customer_phone = models.CharField(max_length=20, verbose_name="Телефон")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    status = models.CharField(max_length=20, default='new', verbose_name="Статус")
    is_paid = models.BooleanField(default=False, verbose_name="Оплачено")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"Заказ №{self.id} от {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    size = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
