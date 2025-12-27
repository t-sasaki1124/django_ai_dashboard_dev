from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import Plan, UserPlan


class Command(BaseCommand):
    help = 'ユーザーを指定したプランに設定します'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='ユーザー名')
        parser.add_argument('plan_name', type=str, help='プラン名 (free, pro, enterprise)')

    def handle(self, *args, **options):
        username = options['username']
        plan_name = options['plan_name']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'ユーザー "{username}" が見つかりません。'))
            return

        try:
            plan = Plan.objects.get(name=plan_name)
        except Plan.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'プラン "{plan_name}" が見つかりません。'))
            self.stdout.write(self.style.WARNING('利用可能なプラン: free, pro, enterprise'))
            return

        # UserPlanを取得または作成
        user_plan, created = UserPlan.objects.get_or_create(
            user=user,
            defaults={'plan': plan, 'is_active': True}
        )

        if not created:
            # 既存のプランを更新
            user_plan.plan = plan
            user_plan.is_active = True
            user_plan.save()
            self.stdout.write(self.style.SUCCESS(
                f'ユーザー "{username}" のプランを "{plan.display_name}" に更新しました。'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'ユーザー "{username}" を "{plan.display_name}" プランに設定しました。'
            ))

