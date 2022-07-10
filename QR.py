# qr code regis sw
# | IMPORT SECTION
from types import NoneType
from typing import Tuple, Union
import qrcode
import shortuuid

# | FUNCTIONS
def create_qr_code(
    data: str,
    version: Union[NoneType, int] = None,
    error_correction: int = qrcode.constants.ERROR_CORRECT_M,
    box_size: int = 10,
    border: int = 4,
    fit: bool = True,
    fill_color: Union[str, Tuple[int, int, int]] = "black",
    back_color: Union[str, Tuple[int, int, int]] = "white",
):
    qr = qrcode.QRCode(
        version=version,
        error_correction=error_correction,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)

    if version is None:
        fit = True
    qr.make(fit=fit)

    return qr.make_image(fill_color=fill_color, back_color=back_color)


# | MAIN
if __name__ == "__main__":
    img = create_qr_code(
        "This is a test message. 0123456789 || นี่คือข้อความทดสอบ",
        box_size=15,
        fill_color="black",
        back_color="#E62B1E",
    )
    img.save("tmp.jpg")
