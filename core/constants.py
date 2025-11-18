from django.db import models

class ProductLine(models.TextChoices):
        STORE = 'RS', 'Rio Store'
        FERRISARITO = 'FS', 'Ferrisariato'
        COMISARIATO = 'CS', 'Comisariato'

class ProductIva(models.IntegerChoices):
    ZERO = 0, '0%'
    FIVE = 5, '5%'
    FIFTEEN = 15, '15%'

class InvoicePaymentMethod(models.TextChoices):
    CASH = 'EF', 'Efectivo'
    CHECK = 'CH', 'Cheque'
    CARD = 'TJ', 'Tarjeta'
    CREDIT = 'CR', 'Crédito'

class CustomerGender(models.TextChoices):
    MALE = 'M', 'Masculino'
    FEMALE = 'F', 'Femenino'