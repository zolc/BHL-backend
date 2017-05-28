import graphene
from sys import stderr
from graphene import relay
from . import app, mongo
import jwt
import sys

from .logic import (
    add_to_users,
    sign_in,
    self_info,
    create_group,
    add_to_info,
    add_to_tasks,
    add_admin_to_group,
    register_to_group,
    remove_admin_from_group,
    remove_from_group,
    delete_group,
    toggle_task_completed,
    toggle_task_important,
    change_settings,
    send_mail_notification,
    text_message)


class User(graphene.ObjectType):
    class Meta:
        interfaces = (relay.Node,)

    _id = graphene.String()
    username = graphene.String()
    email = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()
    phone = graphene.String()
    pass_hash = graphene.String()
    groups = graphene.List(lambda: Group)
    last_online = graphene.String()

    tasks = graphene.List(lambda: Task)
    info = graphene.List(lambda: Info)

    def resolve_groups(self, args, context, info):
        groups = []
        group_id_list = mongo.db.users.find_one({"_id": self._id})['groups']
        for group_id in group_id_list:
            result = mongo.db.groups.find_one({"_id": group_id})
            result['current_user_id'] = self._id
            groups.append(result)
        if len(groups) != 0:
            return [Group(**kwargs) for kwargs in groups]
        return None

    def resolve_tasks(self, args, context, info):
        tasks = []
        for group_id in self.groups:
            tasks_from_group = mongo.db.tasks.find({'group_id': group_id})
            for task in tasks_from_group:
                task['current_user_id'] = self._id
                if self._id in task['users_important']:
                    task['highlighted'] = True
                else:
                    task['highlighted'] = False
                if self._id in task['users_completed']:
                    task['done'] = True
                else:
                    task['done'] = False
                tasks.append(task)
        return [Task(**kwargs) for kwargs in tasks]

    def resolve_info(self, args, context, info):
        info_list = []
        for group_id in self.groups:
            info_from_group = mongo.db.info.find({'group_id': group_id})
        for info in info_from_group:
            info_list.append(info)
        return [Info(**kwargs) for kwargs in info_list]


class Group(graphene.ObjectType):
    class Meta:
        interfaces = (relay.Node,)

    _id = graphene.String()
    name = graphene.String()
    password = graphene.String()
    admins = graphene.List(lambda: User)
    users = graphene.List(lambda: User)
    completed_tasks = graphene.List(lambda: Task)
    uncompleted_tasks = graphene.List(lambda: Task)
    info = graphene.List(lambda: Info)
    current_user_id = graphene.String()

    def resolve_users(self, args, context, info):
        users = []
        user_id_list = mongo.db.groups.find_one({"_id": self._id})['users']
        for user_id in user_id_list:
            result = mongo.db.users.find_one({"_id": user_id})
            users.append(result)
        if len(users) != 0:
            return [User(**kwargs) for kwargs in users]
        return None

    def resolve_admins(self, args, context, info):
        users = []
        user_id_list = mongo.db.groups.find_one({"_id": self._id})['admins']
        for user_id in user_id_list:
            result = mongo.db.users.find_one({"_id": user_id})
            users.append(result)
        if len(users) != 0:
            return [User(**kwargs) for kwargs in users]
        return None

    def resolve_completed_tasks(self, args, context, info):
        tasks = []
        tasks_from_group = mongo.db.tasks.find({'group_id': self._id})
        for task in tasks_from_group:
            task['current_user_id'] = self.current_user_id
            if self.current_user_id in task['users_important']:
                task['highlighted'] = True
            else:
                task['highlighted'] = False
            if self.current_user_id in task['users_completed']:
                task['done'] = True
                tasks.append(task)
        return [Task(**kwargs) for kwargs in tasks]

    def resolve_uncompleted_tasks(self, args, context, info):
        tasks = []
        tasks_from_group = mongo.db.tasks.find({'group_id': self._id})
        for task in tasks_from_group:
            task['current_user_id'] = self.current_user_id
            if self.current_user_id in task['users_important']:
                task['highlighted'] = True
            else:
                task['highlighted'] = False
            if self.current_user_id not in task['users_completed']:
                task['done'] = True
                tasks.append(task)

        return [Task(**kwargs) for kwargs in tasks]

    def resolve_info(self, args, context, info):
        info_list = []
        info_from_group = mongo.db.info.find({'group_id': self._id})
        for info in info_from_group:
            info_list.append(info)
        return [Info(**kwargs) for kwargs in info_list]


class Task(graphene.ObjectType):
    class Meta:
        interfaces = (relay.Node,)

    _id = graphene.String()
    creator = graphene.String()
    group_id = graphene.String()
    users_completed = graphene.List(lambda: User)
    users_important = graphene.List(lambda: User)
    title = graphene.String()
    description = graphene.String()
    published_date = graphene.String()
    due_date = graphene.String()
    done = graphene.Boolean()
    highlighted = graphene.Boolean()
    group = graphene.Field(lambda: Group)
    current_user_id = graphene.String()

    def resolve_group(self, args, context, info):
        result = mongo.db.groups.find_one({'_id': self.group_id})
        result['current_user_id'] = self.current_user_id
        return Group(**result)


class Info(graphene.ObjectType):
    class Meta:
        interfaces = (relay.Node,)

    _id = graphene.String()
    group = Group()
    title = graphene.String()
    description = graphene.String()
    published_date = graphene.String()
    creator = graphene.String()
    group_id = graphene.String()


class Query(graphene.ObjectType):
    users = graphene.List(User,
                          _id=graphene.String(),
                          username=graphene.String()
                          )
    groups = graphene.List(Group,
                           _id=graphene.String(),
                           name=graphene.String(),
                           )


class ChangeSettings(graphene.Mutation):
    class Input:
        token = graphene.String(required=True)
        email = graphene.String(required=False)
        phone = graphene.String(required=False)
        password = graphene.String(required=False)

    success = graphene.Boolean()

    @staticmethod
    def mutate(root, input, context, info):
        token = input.get('token')
        email = input.get('email')
        phone = input.get('phone')
        password = input.get('password')
        result = change_settings(token, email, phone, password)
        return ChangeSettings(success=result)


class SignUp(graphene.Mutation):
    class Input:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=True)
        first_name = graphene.String(required=False)
        last_name = graphene.String(required=False)
        phone = graphene.String(required=False)

    success = graphene.Boolean()

    @staticmethod
    def mutate(root, input, context, info):
        username = input.get('username')
        password = input.get('password')
        email = input.get('email')
        first_name = input.get('first_name')
        last_name = input.get('last_name')
        phone = input.get('phone')
        result = add_to_users(username, password, email, first_name, last_name, phone)
        return SignUp(success=result)


class AddTask(graphene.Mutation):
    class Input:
        token = graphene.String(required=True)
        group_id = graphene.String(required=True)
        title = graphene.String(required=True)
        description = graphene.String(required=False)
        due_date = graphene.String(required=False)

    success = graphene.Boolean()

    @staticmethod
    def mutate(root, input, context, info):
        group_id = input.get('group_id')
        title = input.get('title')
        description = input.get('description')
        due_date = input.get('due_date')
        token = input.get('token')
        result = add_to_tasks(token, group_id, title, due_date,description)
        return AddTask(success=result)


class SignIn(graphene.Mutation):
    class Input:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    success = graphene.Boolean()
    token = graphene.String()

    @staticmethod
    def mutate(root, input, context, info):
        username = input.get('username')
        password = input.get('password')
        (success, token) = sign_in(username, password)
        return SignIn(success=success, token=token)


class SelfInfo(graphene.Mutation):
    class Input:
        token = graphene.String(required=True)

    user = graphene.Field(User)

    @staticmethod
    def mutate(root, input, context, info):
        token = input.get('token')
        result = self_info(token)
        return SelfInfo(user=result)


class CreateGroup(graphene.Mutation):
    class Input:
        token = graphene.String(required=True)
        group_name = graphene.String(required=True)
        password = graphene.String(required=True)

    success = graphene.String()

    @staticmethod
    def mutate(root, input, context, info):
        token = input.get('token')
        group_name = input.get('group_name')
        password = input.get('password')
        result = create_group(token, group_name, password)
        return CreateGroup(success=result)


class AddAdminToGroup(graphene.Mutation):
    class Input:
        token = graphene.String(required=True)
        username = graphene.String(required=True)
        group_id = graphene.String(required=True)

    success = graphene.Boolean()

    @staticmethod
    def mutate(root, input, context, info):
        token = input.get('token')
        username = input.get('username')
        group_id = input.get('group_id')
        result = add_admin_to_group(token, username, group_id)
        return AddAdminToGroup(success=result)


class RemoveAdminFromGroup(graphene.Mutation):
    class Input:
        token = graphene.String(required=True)
        user_id = graphene.String(required=True)
        group_id = graphene.String(required=True)

    success = graphene.Boolean()

    @staticmethod
    def mutate(root, input, context, info):
        token = input.get('token')
        user_id = input.get('user_id')
        group_id = input.get('group_id')
        result = remove_admin_from_group(token, user_id, group_id)
        return RemoveAdminFromGroup(success=result)


class RegisterToGroup(graphene.Mutation):
    class Input:
        token = graphene.String(required=True)
        group_id = graphene.String(required=True)
        password = graphene.String(required=True)

    success = graphene.String()

    @staticmethod
    def mutate(root, input, context, info):
        token = input.get('token')
        group_id = input.get('group_id')
        password = input.get('password')
        result = register_to_group(token, group_id, password)
        return RegisterToGroup(success=result)


class RemoveFromGroup(graphene.Mutation):
    class Input:
        token = graphene.String(required=True)
        group_id = graphene.String(required=True)

    success = graphene.Boolean()

    @staticmethod
    def mutate(root, input, context, info):
        token = input.get('token')
        group_id = input.get('group_id')
        result = remove_from_group(token, group_id)
        return RemoveFromGroup(success=result)


class AddInfo(graphene.Mutation):
    class Input:
        token = graphene.String(required=True)
        group_id = graphene.String(required=True)
        title = graphene.String(required=True)
        description = graphene.String(required=False)

    success = graphene.Boolean()

    @staticmethod
    def mutate(root, input, context, info):
        token = input.get('token')
        group_id = input.get('group_id')
        title = input.get('title')
        description = input.get('description')
        result = add_to_info(token, group_id, title, description)
        return AddTask(success=result)


class DeleteGroup(graphene.Mutation):
    class Input:
        token = graphene.String(required=True)
        group_id = graphene.String(required=True)

    success = graphene.Boolean()

    @staticmethod
    def mutate(root, input, context, info):
        token = input.get('token')
        group_id = input.get('group_id')
        result = delete_group(token, group_id)
        return DeleteGroup(success=result)


class ToggleComplete(graphene.Mutation):
    class Input:
        token = graphene.String()
        task_id = graphene.String()

    success = graphene.Boolean()

    @staticmethod
    def mutate(root, input, context, info):
        token = input.get('token')
        task_id = input.get('task_id')
        result = toggle_task_completed(token, task_id)
        return ToggleComplete(success=result)


class ToggleImportant(graphene.Mutation):
    class Input:
        token = graphene.String()
        task_id = graphene.String()

    success = graphene.Boolean()

    @staticmethod
    def mutate(root, input, context, info):
        token = input.get('token')
        task_id = input.get('task_id')
        result = toggle_task_important(token, task_id)
        return ToggleImportant(success=result)


# Only for debugging
class SendMail(graphene.Mutation):
    class Input:
        token = graphene.String()
        task_id = graphene.String()

    success = graphene.Boolean()

    @staticmethod
    def mutate(root, input, context, info):
        token = input.get('token')
        task_id = input.get('task_id')
        result = send_mail_notification(token, task_id)
        return SendMail(success=result)


# Only for debugging
class TextMessage(graphene.Mutation):
    class Input:
        token = graphene.String()
        task_id = graphene.String()

    success = graphene.Boolean()

    @staticmethod
    def mutate(root, input, context, info):
        token = input.get('token')
        task_id = input.get('task_id')
        result = text_message(token, task_id)
        return TextMessage(success=result)


class Mutation(graphene.ObjectType):
    SignUp = SignUp.Field()
    AddTask = AddTask.Field()
    AddInfo = AddInfo.Field()
    SignIn = SignIn.Field()
    SelfInfo = SelfInfo.Field()
    CreateGroup = CreateGroup.Field()
    RegisterToGroup = RegisterToGroup.Field()
    AddAdminToGroup = AddAdminToGroup.Field()
    RemoveAdminFromGroup = RemoveAdminFromGroup.Field()
    RemoveFromGroup = RemoveFromGroup.Field()
    DeleteGroup = DeleteGroup.Field()
    ToggleComplete = ToggleComplete.Field()
    ToggleImportant = ToggleImportant.Field()
    ChangeSettings = ChangeSettings.Field()
    SendMail = SendMail.Field()
    TextMessage = TextMessage.Field()


schema = graphene.Schema(query=Query, auto_camelcase=False, mutation=Mutation)
