from django.core.management.base import BaseCommand
from myapp.models import Plan


class Command(BaseCommand):
    help = 'デフォルトのプラン（無料、Pro、Enterprise）を作成します'

    def handle(self, *args, **options):
        plans_data = [
            {
                'name': 'free',
                'display_name': '無料プラン',
                'price': 0,
                'is_premium': False,
                'description': '基本的な機能が利用できる無料プランです。'
            },
            {
                'name': 'pro',
                'display_name': 'Proプラン',
                'price': 980,
                'is_premium': True,
                'description': 'レポート出力など、高度な機能が利用できるProプランです。'
            },
            {
                'name': 'enterprise',
                'display_name': 'Enterpriseプラン',
                'price': 5000,
                'is_premium': True,
                'description': 'すべての機能が利用できるEnterpriseプランです。'
            },
        ]

        for plan_data in plans_data:
            plan, created = Plan.objects.get_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f'プラン "{plan.display_name}" を作成しました。'
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f'プラン "{plan.display_name}" は既に存在します。'
                ))

