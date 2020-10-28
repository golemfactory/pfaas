from pfaas import remote_fn
import argparse
import asyncio
import math
import png

@remote_fn()
def compute_rectangle(n: int, start_y: int, end_y: int, width: int, height: int) -> (int, [int]):
    RE_START: float = -2.0
    RE_END: float = 1.0
    IM_START: float = -1.0
    IM_END: float = 1.0

    def mandelbrot(c: complex) -> int:
        MAX_ITER: int = 255

        z = 0
        niter = 0
        while abs(z) <= 2.0 and niter < MAX_ITER:
            z = pow(z, 2) + c
            niter += 1

        return MAX_ITER - niter

    output = []
    for y in range(start_y, end_y):
        for x in range(0, width):
            c = complex(RE_START + (x / width) * (RE_END - RE_START), IM_START + (y / height) * (IM_END - IM_START))
            output += [mandelbrot(c)]

    return (n, output)

async def main(width: int, height: int, in_parallel: int):
    max_row_size = math.ceil(height / in_parallel)

    chunks = []
    for n in range(0, in_parallel):
        start_y = n * max_row_size
        end_y = height if start_y + max_row_size > height else start_y + max_row_size
        chunks += [(n, start_y, end_y)]

    futs = []
    for chunk in chunks:
        futs += [compute_rectangle(*chunk, width, height)]

    output = await asyncio.gather(*futs)
    output = sorted(output, key=lambda x: x[0])

    with open("mandelbrot.png", "wb") as f:
        writer = png.Writer(width=width, height=height, greyscale=True, bitdepth=8)
        pixels = []
        for (_, out) in output:
            pixels += out
        writer.write_array(f, pixels)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generates a Mandelbrot set and saves as PNG.")
    parser.add_argument("--width", dest="width", default=600, help="Width of the image to generate.")
    parser.add_argument("--height", dest="height", default=400, help="Height of the image to generate.")
    parser.add_argument("--in_parallel", dest="in_parallel", default=4, help="Maximum number of parallel computations to run.")
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    task = loop.create_task(main(int(args.width), int(args.height), int(args.in_parallel)))
    
    try:
        asyncio.get_event_loop().run_until_complete(task)
    except (Exception, KeyboardInterrupt) as e:
        print(e)
        task.cancel()
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.3))

