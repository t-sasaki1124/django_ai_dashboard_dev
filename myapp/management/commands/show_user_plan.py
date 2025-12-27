from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import UserPlan


class Command(BaseCommand):
    help = 'ユーザーの現在のプランを表示します'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='ユーザー名')

    def handle(self, *args, **options):
        username = options['username']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'ユーザー "{username}" が見つかりません。'))
            return

        try:
            user_plan = UserPlan.objects.get(user=user, is_active=True)
            plan = user_plan.plan
            self.stdout.write(self.style.SUCCESS(
                f'\nユーザー: {user.username}'
            ))
            self.stdout.write(f'プラン: {plan.display_name}')
            self.stdout.write(f'価格: {plan.price}円/月')
            self.stdout.write(f'有料プラン: {"はい" if plan.is_premium else "いいえ"}')
            self.stdout.write(f'開始日時: {user_plan.started_at}')
            if user_plan.expires_at:
                self.stdout.write(f'有効期限: {user_plan.expires_at}')
            else:
                self.stdout.write('有効期限: 無期限')
        except UserPlan.DoesNotExist:
            self.stdout.write(self.style.WARNING(
                f'ユーザー "{username}" にはプランが設定されていません（無料プラン）。'
            ))

