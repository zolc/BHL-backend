import graphene
from sys import stderr
from graphene import relay
from . import app, mongo
import jwt
import sys

from .logic import add_to_users, sign_in, self_info, create_group, add_to_info, add_to_tasks, add_admin_to_group, \
    register_to_group, remove_admin_from_group, remove_from_group


class User(graphene.ObjectType):
    class Meta:
        interfaces = (relay.Node,)

    _id = graphene.ID()
    username = graphene.String()
    email = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()
    phone = graphene.String()
    pass_hash = graphene.String()
    groups = graphene.List(lambda: Group)
    last_online = graphene.String()

    def resolve_groups(self, args, context, info):
        groups = []
        group_id_list = mongo.db.users.find_one({"username": self.username})['groups']
        for group_name in group_id_list:
            result = mongo.db.groups.find_one({"name": group_name})
            groups.append(result)
        if len(groups) != 0:
            return [Group(**kwargs) for kwargs in groups]
        return None


class Group(graphene.ObjectType):
    class Meta:
        interfaces = (relay.Node,)

    _id = graphene.ID()
    name = graphene.String()
    password = graphene.String()
    admins = graphene.List(lambda: User)
    users = graphene.List(lambda: User)

    def resolve_users(self, args, context, info):
        users = []
        user_id_list = mongo.db.groups.find_one({"name": self.name})['users']
        for username in user_id_list:
            result = mongo.db.users.find_one({"username": username})
            users.append(result)
        if len(users) != 0:
            return [User(**kwargs) for kwargs in users]
        return None

    def resolve_admins(self, args, context, info):
        users = []
        user_id_list = mongo.db.groups.find_one({"name": self.name})['admins']
        for username in user_id_list:
            result = mongo.db.users.find_one({"username": username})
            users.append(result)
        if len(users) != 0:
            return [User(**kwargs) for kwargs in users]
        return None


class Task(graphene.ObjectType):
    class Meta:
        interfaces = (relay.Node,)

    _id = graphene.ID()
    title = graphene.String()
    description = graphene.String()
    group = Group()
    published_date = graphene.String()
    due_date = graphene.String()
    done = graphene.Boolean()
    highlighted = graphene.Boolean()


class Info(graphene.ObjectType):
    class Meta:
        interfaces = (relay.Node,)

    _id = graphene.ID()
    group = Group()
    title = graphene.String()
    description = graphene.String()
    published_date = graphene.String()


class Query(graphene.ObjectType):
    users = graphene.List(User,
                          _id=graphene.ID(),
                          username=graphene.String()
                          )
    groups = graphene.List(Group,
                           _id=graphene.ID(),
                           name=graphene.String(),
                           )


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
        group_name = graphene.String(required=True)
        title = graphene.String(required=True)
        description = graphene.String(required=False)
        due_date = graphene.String(required=False)

    success = graphene.Boolean()

    @staticmethod
    def mutate(root, input, context, info):
        group_name = input.get('group_name')
        title = input.get('title')
        description = input.get('description')
        due_date = input.get('due_date')
        token = input.get('token')
        result = add_to_tasks(token, group_name, title, description, due_date)
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
        print(password, file=sys.stderr)
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
        group_name = graphene.String(required=True)

    success = graphene.Boolean()

    @staticmethod
    def mutate(root, input, context, info):
        token = input.get('token')
        username = input.get('username')
        group_name = input.get('group_name')
        result = add_admin_to_group(token, username, group_name)
        return AddAdminToGroup(success=result)


class RemoveAdminFromGroup(graphene.Mutation):
    class Input:
        token = graphene.String(required=True)
        username = graphene.String(required=True)
        group_name = graphene.String(required=True)

    success = graphene.Boolean()

    @staticmethod
    def mutate(root, input, context, info):
        token = input.get('token')
        username = input.get('username')
        group_name = input.get('group_name')
        result = remove_admin_from_group(token, username, group_name)
        return RemoveAdminFromGroup(success=result)


class RegisterToGroup(graphene.Mutation):
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
        result = register_to_group(token, group_name, password)
        return RegisterToGroup(success=result)


class RemoveFromGroup(graphene.Mutation):
    class Input:
        token = graphene.String(required=True)
        group_name = graphene.String(required=True)

    success = graphene.Boolean()

    @staticmethod
    def mutate(root, input, context, info):
        token = input.get('token')
        group_name = input.get('group_name')
        result = remove_from_group(token, group_name)
        return RemoveFromGroup(success=result)


class AddInfo(graphene.Mutation):
    class Input:
        token = graphene.String(required=True)
        group_name = graphene.String(required=True)
        title = graphene.String(required=True)
        description = graphene.String(required=False)

    success = graphene.Boolean()

    @staticmethod
    def mutate(root, input, context, info):
        token = input.get('token')
        group_name = input.get('group_name')
        title = input.get('title')
        description = input.get('description')
        result = add_to_info(token, group_name, title, description)
        return AddTask(success=result)


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

schema = graphene.Schema(query=Query, auto_camelcase=False, mutation=Mutation)
