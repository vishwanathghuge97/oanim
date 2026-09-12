//! oanim-core: hot loops for the oanim engine (users stay in Python).
//! Slice 1: scatter-add kernels replacing `np.add.at` on the trail canvas.
//! Slice 2: fused form-step (analytic flow + staggered spring + integrate).
use numpy::{PyReadonlyArray1, PyReadonlyArray2, PyReadwriteArray2};
use pyo3::prelude::*;
use rayon::prelude::*;

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
    m.add_function(wrap_pyfunction!(step_form, m)?)?;
    Ok(())
}

#[inline]
fn sstep(a: f32, b: f32, x: f32) -> f32 {
    let t = ((x - a) / (b - a).max(1e-6)).clamp(0.0, 1.0);
    t * t * (3.0 - 2.0 * t)
}

/// Fused morph step: per-particle staggered activation, analytic curl-ish flow
/// (decaying), underdamped spring to target, speed cap, semi-implicit integrate.
/// Mirrors `FlowParticles.form` math. Trig in f64 (like numpy) then back to f32.
/// Returns (mean_act, mean_dist) for the reveal logic (kept in Python).
#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn step_form(
    mut pos: PyReadwriteArray2<f32>,
    mut vel: PyReadwriteArray2<f32>,
    targets: PyReadonlyArray2<f32>,
    nx: PyReadonlyArray1<f32>,
    rand: PyReadonlyArray1<f32>,
    ts: f32,
    t_glob: f32,
    dt: f32,
    sweep: f32,
    form_dur: f32,
    k: f32,
    c: f32,
    boost: f32,
    damp: f32,
) -> PyResult<(f32, f32)> {
    let pos_s = pos.as_slice_mut()?;
    let vel_s = vel.as_slice_mut()?;
    let tgt_s = targets.as_slice()?;
    let nx_s = nx.as_slice()?;
    let rnd_s = rand.as_slice()?;
    let n = nx_s.len();
    debug_assert_eq!(pos_s.len(), 2 * n);
    debug_assert_eq!(vel_s.len(), 2 * n);
    debug_assert_eq!(tgt_s.len(), 2 * n);
    debug_assert_eq!(rnd_s.len(), n);

    // Pass 1: activation per particle (+ mean for the speed cap).
    let act_sum: f32 = (0..n)
        .into_par_iter()
        .map(|i| sstep(nx_s[i] * sweep + rnd_s[i], nx_s[i] * sweep + rnd_s[i] + 0.7, ts))
        .sum();
    let mean_act = act_sum / n.max(1) as f32;
    let flow_w = 1.0 - sstep(0.0, form_dur * 0.6, ts) * 0.95;
    let cap = 460.0 - 260.0 * mean_act;
    // f32 trig: ~3x faster than f64, error ~1e-7 (well inside 1e-3 parity).
    let tg = t_glob;
    let dtf = dt;

    // Pass 2: flow + spring + cap + integrate (+ mean distance).
    // Disjoint 2-elem chunks keep threads alias-free; nx/rand are shared reads.
    let dist_sum: f32 = pos_s
        .par_chunks_mut(2)
        .zip(vel_s.par_chunks_mut(2))
        .zip(tgt_s.par_chunks(2))
        .enumerate()
        .map(|(i, ((p, v), g))| {
            let x = p[0];
            let y = p[1];
            let tx = g[0];
            let ty = g[1];
            let a0 = nx_s[i] * sweep + rnd_s[i];
            let act = sstep(a0, a0 + 0.7, ts);
            let fx = ((y * 0.012 + tg * 0.9).sin() + 0.5 * ((x + y) * 0.006 - tg * 0.6).sin())
                * 55.0
                * flow_w
                * boost;
            let fy = ((x * 0.011 - tg * 0.7).cos() + 0.5 * ((x - y) * 0.007 + tg * 0.5).cos())
                * 55.0
                * flow_w
                * boost;
            let dx = tx - x;
            let dy = ty - y;
            let ka = k * act;
            let ca = c * act;
            let mut vx = v[0];
            let mut vy = v[1];
            vx += (fx * 0.35 + dx * ka - vx * ca) * dtf;
            vy += (fy * 0.35 + dy * ka - vy * ca) * dtf;
            vx *= damp;
            vy *= damp;
            let sp = (vx * vx + vy * vy).sqrt();
            let s = (cap / sp.max(1e-6)).min(1.0);
            vx *= s;
            vy *= s;
            p[0] = x + vx * dtf;
            p[1] = y + vy * dtf;
            v[0] = vx;
            v[1] = vy;
            (dx * dx + dy * dy).sqrt()
        })
        .sum();
    Ok((mean_act, dist_sum / n.max(1) as f32))
}
