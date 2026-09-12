//! oanim-core: hot loops for the oanim engine (users stay in Python).
//! Slice 1: parallel-free scatter-add replacing `np.add.at` on the trail canvas.
use numpy::{PyReadonlyArray1, PyReadwriteArray2};
use pyo3::prelude::*;

/// Add `vals[i]` into `canvas[ys[i], xs[i]]`, skipping out-of-bounds points.
/// All arrays must be contiguous; canvas is float32 [H, W].
#[pyfunction]
fn splat_add(
    mut canvas: PyReadwriteArray2<f32>,
    xs: PyReadonlyArray1<i32>,
    ys: PyReadonlyArray1<i32>,
    vals: PyReadonlyArray1<f32>,
) -> PyResult<()> {
    let mut c = canvas.as_array_mut();
    let (h, w) = (c.nrows(), c.ncols());
    let xs = xs.as_slice()?;
    let ys = ys.as_slice()?;
    let vs = vals.as_slice()?;
    let n = xs.len().min(ys.len()).min(vs.len());
    let ptr = c.as_mut_ptr();
    // SAFETY: indices are bounds-checked below; single thread, no aliasing issue
    // since canvas is exclusively borrowed via PyReadwriteArray2.
    for i in 0..n {
        let x = xs[i];
        let y = ys[i];
        if x >= 0 && (x as usize) < w && y >= 0 && (y as usize) < h {
            unsafe {
                *ptr.add(y as usize * w + x as usize) += vs[i];
            }
        }
    }
    Ok(())
}

/// Fused stamp: center value `b` + optional right/down glow `g` in one pass.
/// Mirrors Scene._draw's even-frame glow without a second Python call.
#[pyfunction]
fn splat_add_glow(
    mut canvas: PyReadwriteArray2<f32>,
    xs: PyReadonlyArray1<i32>,
    ys: PyReadonlyArray1<i32>,
    b: f32,
    g: f32,
) -> PyResult<()> {
    let mut c = canvas.as_array_mut();
    let (h, w) = (c.nrows(), c.ncols());
    let xs = xs.as_slice()?;
    let ys = ys.as_slice()?;
    let n = xs.len().min(ys.len());
    let ptr = c.as_mut_ptr();
    for i in 0..n {
        let x = xs[i];
        let y = ys[i];
        if x >= 0 && (x as usize) < w && y >= 0 && (y as usize) < h {
            let xu = x as usize;
            let yu = y as usize;
            unsafe {
                *ptr.add(yu * w + xu) += b;
                if g != 0.0 {
                    if yu + 1 < h {
                        *ptr.add((yu + 1) * w + xu) += g;
                    }
                    if xu + 1 < w {
                        *ptr.add(yu * w + xu + 1) += g;
                    }
                }
            }
        }
    }
    Ok(())
}

#[pymodule]
fn oanim_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(splat_add, m)?)?;
    m.add_function(wrap_pyfunction!(splat_add_glow, m)?)?;
    Ok(())
}
