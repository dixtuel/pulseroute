from fastapi import APIRouter, HTTPException, Query, Response

from pulseroute.common.qr_generator import generate_qr_ascii, generate_qr_png, generate_qr_svg

router = APIRouter(prefix="/qr", tags=["QR Code Generator"])


@router.get("")
async def get_qr_code(
    data: str = Query(..., description="Target URL or text to encode"),
    format: str = Query("png", pattern="^(png|svg|ascii)$"),
    fill_color: str = "black",
    back_color: str = "white",
):
    if format == "png":
        png_bytes = generate_qr_png(data, fill_color=fill_color, back_color=back_color)
        return Response(content=png_bytes, media_type="image/png")
    elif format == "svg":
        svg_str = generate_qr_svg(data)
        return Response(content=svg_str, media_type="image/svg+xml")
    elif format == "ascii":
        ascii_art = generate_qr_ascii(data)
        return Response(content=ascii_art, media_type="text/plain")
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")
