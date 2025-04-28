import graphene
from graphene_django.types import DjangoObjectType
from .models import CustomUser, Gig
from .forms import GigForm
import graphql_jwt

# GraphQL Types
class UserType(DjangoObjectType):
    class Meta:
        model = CustomUser
        fields = ("id", "username", "email", "is_seller")

class GigType(DjangoObjectType):
    class Meta:
        model = Gig
        fields = ("id", "title", "description", "price", "seller", "created_at")

# Queries
class Query(graphene.ObjectType):
    all_gigs = graphene.List(GigType)
    gig = graphene.Field(GigType, id=graphene.Int())
    all_users = graphene.List(UserType)
    user = graphene.Field(UserType, id=graphene.Int())

    def resolve_all_gigs(root, info):
        return Gig.objects.select_related("seller").all()

    def resolve_gig(root, info, id):
        return Gig.objects.get(pk=id)

    def resolve_all_users(root, info):
        return CustomUser.objects.all()

    def resolve_user(root, info, id):
        return CustomUser.objects.get(pk=id)

class RegisterUser(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    user = graphene.Field(UserType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, username, email, password):
        user = CustomUser(username=username, email=email)
        user.set_password(password)
        try:
            user.save()
            return RegisterUser(user=user, success=True, errors=[])
        except Exception as e:
            return RegisterUser(user=None, success=False, errors=[str(e)])

class CreateGig(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        description = graphene.String(required=True)
        price = graphene.String(required=True)  # Price as string for DecimalField

    success = graphene.Boolean()
    gig = graphene.Field(GigType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, title, description, price):
        user = info.context.user
        if not user.is_authenticated:
            return CreateGig(success=False, gig=None, errors=["Authentication required."])

        form = GigForm(data={
            "title": title,
            "description": description,
            "price": price,
        })

        if form.is_valid():
            gig = form.save(commit=False)
            gig.seller = user
            gig.save()
            return CreateGig(success=True, gig=gig, errors=[])
        else:
            error_list = [f"{field}: {error[0]['message']}" for field, error in form.errors.get_json_data().items()]
            return CreateGig(success=False, gig=None, errors=error_list)


class UpdateGig(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        title = graphene.String()
        description = graphene.String()
        price = graphene.String()

    success = graphene.Boolean()
    gig = graphene.Field(GigType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, id, title=None, description=None, price=None):
        try:
            gig = Gig.objects.get(pk=id)
            user = info.context.user

            if gig.seller != user:
                return UpdateGig(success=False, gig=None, errors=["You are not the owner of this gig."])

            if title: gig.title = title
            if description: gig.description = description
            if price: gig.price = price

            gig.save()
            return UpdateGig(success=True, gig=gig, errors=[])

        except Gig.DoesNotExist:
            return UpdateGig(success=False, gig=None, errors=["Gig not found."])

class DeleteGig(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        try:
            gig = Gig.objects.get(pk=id)
            user = info.context.user

            if gig.seller != user:
                return DeleteGig(success=False, errors=["You are not authorized to delete this gig."])

            gig.delete()
            return DeleteGig(success=True, errors=[])

        except Gig.DoesNotExist:
            return DeleteGig(success=False, errors=["Gig not found."]) 

class Mutation(graphene.ObjectType):
    register_user = RegisterUser.Field()
    create_gig = CreateGig.Field()
    update_gig = UpdateGig.Field()
    delete_gig = DeleteGig.Field()

    # token Authentication
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()