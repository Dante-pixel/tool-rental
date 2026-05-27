from django.contrib import admin
from .models import Category, SubCategory, Tool, ToolImage, ToolVariant, RentalTariff, ToolQuantity, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)


# Инлайны для карточки ТОВАРА (Внутри самого инструмента)
class ToolImageInline(admin.TabularInline):
    model = ToolImage
    extra = 1


class ToolVariantInline(admin.TabularInline):
    model = ToolVariant
    extra = 1


class RentalTariffInline(admin.TabularInline):
    model = RentalTariff
    extra = 1


class ToolQuantityInline(admin.TabularInline):
    model = ToolQuantity
    extra = 1
    max_num = 1  # Больше одной строки для количества не нужно


@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'subcategory', 'is_available')
    list_filter = ('category', 'subcategory', 'is_available')
    search_fields = ('title', 'description')

    # Выводим ВСЕ 4 таблицы на одной странице друг за другом!
    inlines = [
        ToolImageInline,
        ToolVariantInline,
        RentalTariffInline,
        ToolQuantityInline
    ]


# --- НОВЫЙ БЛОК: ИНЛАЙНЫ И НАСТРОЙКА ДЛЯ ЗАКАЗОВ КЛИЕНТОВ ---

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0  # Чтобы пустые строки не создавались, только то, что купил клиент
    # Делаем поля доступными только для чтения, чтобы случайно не изменить параметры заказанного инструмента
    readonly_fields = ('title', 'size', 'price', 'quantity')
    can_delete = False  # Запрещаем удалять отдельные товары из заказа через админку


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Что будет видно в общей таблице всех заказов
    list_display = ('id', 'customer_name', 'customer_phone', 'total_price', 'status', 'created_at')
    # Фильтры справа (удобно смотреть "только новые" или "только оплаченные")
    list_filter = ('status', 'created_at')
    # Поиск по имени, телефону или номеру чека
    search_fields = ('customer_name', 'customer_phone', 'id')
    # Сортировка (новые заказы всегда в самом верху списка)
    ordering = ('-created_at',)

    # Выводим состав заказа (список инструментов) прямо внутрь карточки заказа
    inlines = [OrderItemInline]