import graphene
from graphene_django.types import DjangoObjectType
from .models import CustomUser, Gig, Order, Message
from graphql_jwt.decorators import login_required
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError      
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

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = "__all__"

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

# class for Orders

class CreateOrder(graphene.Mutation):
    class Arguments:
        gig_id = graphene.ID(required=True)
        description = graphene.String(required=False)

    order = graphene.Field(OrderType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @login_required
    def mutate(self, info, gig_id, description=None):
        user = info.context.user

        try:
            gig = Gig.objects.get(pk=gig_id)
        except Gig.DoesNotExist:
            return CreateOrder(success=False, errors=["Gig not found."])

        if gig.seller == user:
            return CreateOrder(success=False, errors=["You cannot order your own gig."])

        order = Order.objects.create(
            buyer=user,
            gig=gig,
            description=description,
            status="pending"
        )

        return CreateOrder(order=order, success=True, errors=[])


class UpdateOrderStatus(graphene.Mutation):
    class Arguments:
        order_id = graphene.ID(required=True)
        status = graphene.String(required=True)

    order = graphene.Field(OrderType)
    errors = graphene.List(graphene.String)

    @login_required
    def mutate(self, info, order_id, status):
        user = info.context.user

        # Check if the order exists
        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            return UpdateOrderStatus(errors=["Order not found"])

        # Check if the user is the seller of the gig
        if order.gig.seller != user:
            return UpdateOrderStatus(errors=["You are not authorized to update this order"])

        # Check if the status is valid
        if status not in ['pending', 'in_progress', 'completed', 'cancelled']:
            return UpdateOrderStatus(errors=["Invalid status"])

        # Update the status
        order.status = status
        order.save()

        return UpdateOrderStatus(order=order, errors=[])


class DeleteOrder(graphene.Mutation):
    class Arguments:
        order_id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @login_required
    def mutate(self, info, order_id):
        user = info.context.user

        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            return DeleteOrder(success=False, errors=["Order not found"])

        # Check if the current user is the buyer of the order
        if order.buyer != user:
            return DeleteOrder(success=False, errors=["You are not authorized to delete this order"])

        # Delete the order
        order.delete()
        return DeleteOrder(success=True, errors=[])


class MessageType(DjangoObjectType):
    class Meta:
        model = Message
        fields = ("id", "order", "sender", "content", "timestamp")

class SendMessage(graphene.Mutation):
    class Arguments:
        order_id = graphene.ID(required=True)
        content = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.Field(MessageType)

    def mutate(self, info, order_id, content):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("You must be logged in to send a message.")
        
        # Ensure the order exists
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            raise Exception("Order not found.")
        
        # Ensure the user is either the buyer or seller of the order
        if user != order.buyer and user != order.seller:
            raise Exception("You are not authorized to send messages for this order.")
        
        # Create the message
        message = Message.objects.create(
            order=order,
            sender=user,
            content=content
        )

        return SendMessage(success=True, message=message)


class Mutation(graphene.ObjectType):
    register_user = RegisterUser.Field()
    create_gig = CreateGig.Field()
    update_gig = UpdateGig.Field()
    delete_gig = DeleteGig.Field()
    create_order = CreateOrder.Field()
    update_order_status = UpdateOrderStatus.Field()
    delete_order = DeleteOrder.Field()
    send_message = SendMessage.Field()    
    
    # JWT Authentication 
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()