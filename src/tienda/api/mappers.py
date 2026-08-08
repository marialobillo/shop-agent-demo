from tienda.api.schemas import CartLineOut, CartOut, SuggestedLineOut, SuggestedOrderOut
from tienda.domain.cartline import CartLine
from tienda.domain.entities.cart import Cart
from tienda.domain.services.suggestion import SuggestedLine


def cart_to_out(cart: Cart) -> CartOut:
    lines = [
        CartLineOut(
            product_id=line.product.product_id,
            name=line.product.name,
            price=line.product.price,
            quantity=line.quantity,
            subtotal=line.subtotal,
        )
        for line in cart.lines.values()
    ]
    return CartOut(lines=lines, total=cart.total)


def suggested_line_to_out(line: SuggestedLine) -> SuggestedLineOut:
    if line.product is None:
        return SuggestedLineOut(status=line.status, source_text=line.source_text, quantity=line.quantity)
    return SuggestedLineOut(
        status=line.status,
        source_text=line.source_text,
        quantity=line.quantity,
        product_id=line.product.product_id,
        name=line.product.name,
        price=line.product.price,
        subtotal=line.product.price * line.quantity,
    )


def suggested_order_to_out(lines: list[SuggestedLine]) -> SuggestedOrderOut:
    return SuggestedOrderOut(lines=[suggested_line_to_out(line) for line in lines])

def cart_line_out(cartline: CartLine) -> CartLineOut:
    return CartLineOut(
        product_id=cartline.product.product_id,
        name=cartline.product.name,
        price=cartline.product.price,
        quantity=cartline.quantity,
        subtotal=cartline.subtotal,
    )