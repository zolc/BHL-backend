import graphene
from sys import stderr
from graphene import relay
from . import app, mongo
import jwt
from .logic import add_to_users


class User(graphene.ObjectType):
    class Meta:
        interfaces = (relay.Node,)

    _id = graphene.ID()
    username = graphene.String()
    email = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()
    phone = graphene.String()


class Group(graphene.ObjectType):
    class Meta:
        interfaces = (relay.Node,)

    _id = graphene.ID()
    name = graphene.String()
    users = graphene.List(lambda: User)

    def resolve_users(self, args, context, info):
        users = []
        user_id_list = mongo.db.groups.find({"_id": self._id})['users']
        for user_id in user_id_list:
            result = mongo.db.users.find_one({"_id": user_id})
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
        due_date= graphene.String(required=False)

    success = graphene.Boolean()

    @staticmethod
    def mutate(root, input, context, info):
        group_name = input.get('group_name')
        title = input.get('title')
        description = input.get('description')
        due_date = input.get('due_date')
        result = add_to_tasks(token, group_name, title, description, due_date)
        return AddTask(success=result)


class Mutation(graphene.ObjectType):
    SignUp = SignUp.Field()
    AddTask = AddTask.Field()


schema = graphene.Schema(query=Query, auto_camelcase=False, mutation=Mutation)