import re
from django.core.management.base import BaseCommand
from customers.models import Customer


def format_mexican_phone(phone_str):
    if not phone_str:
        return ''
    # Remove non-digits and hidden whitespace
    digits = re.sub(r'\D', '', str(phone_str))

    # Strip Mexican country code if present (+521 or +52)
    if len(digits) == 13 and digits.startswith('521'):
        digits = digits[3:]
    elif len(digits) == 12 and digits.startswith('52'):
        digits = digits[2:]

    # Standard 10-digit Mexican format: NNN NNN NNNN
    if len(digits) == 10:
        return f"{digits[:3]} {digits[3:6]} {digits[6:]}"

    return phone_str.strip()


class Command(BaseCommand):
    help = 'Estandariza los números telefónicos de los clientes al formato NNN NNN NNNN'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra los cambios que se realizarían sin modificar la base de datos',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        customers = Customer.objects.all()
        
        updated_count = 0
        already_valid_count = 0
        skipped = []

        self.stdout.write(self.style.NOTICE(f'Procesando {customers.count()} clientes...'))

        for c in customers:
            orig = (c.phone_number or '').strip()
            formatted = format_mexican_phone(orig)

            digits = re.sub(r'\D', '', orig)
            if len(digits) == 13 and digits.startswith('521'):
                digits = digits[3:]
            elif len(digits) == 12 and digits.startswith('52'):
                digits = digits[2:]

            if len(digits) == 10:
                if orig != formatted:
                    self.stdout.write(f'  [ACTUALIZAR] ID {c.id} ({c.name}): "{orig}" -> "{formatted}"')
                    if not dry_run:
                        c.phone_number = formatted
                        c.save(update_fields=['phone_number'])
                    updated_count += 1
                else:
                    already_valid_count += 1
            else:
                skipped.append((c.id, c.name, orig))

        if dry_run:
            self.stdout.write(self.style.WARNING(f'\n[DRY RUN] Se actualizarían {updated_count} teléfonos.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n¡Éxito! Se actualizaron {updated_count} teléfonos.'))

        self.stdout.write(f'Ya formateados correctamente: {already_valid_count}')

        if skipped:
            self.stdout.write(self.style.NOTICE(f'\nTeléfonos no estándar o incompletos ({len(skipped)}):'))
            for cid, name, phone in skipped:
                self.stdout.write(f'  - ID {cid}: {name} -> "{phone}"')
