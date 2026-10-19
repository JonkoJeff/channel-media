/**
 * Negate a vector.
 * @param A
 * @internal
 */
export function neg(A) {
    return [-A[0], -A[1]];
}
/**
 * Add vectors.
 * @param A
 * @param B
 * @internal
 */
export function add(A, B) {
    return [A[0] + B[0], A[1] + B[1]];
}
/**
 * Add vectors into an existing output vector (allocation-free).
 * @param out Output vector to mutate
 * @param A
 * @param B
 * @internal
 */
export function addInto(out, A, B) {
    out[0] = A[0] + B[0];
    out[1] = A[1] + B[1];
    return out;
}
/**
 * Subtract vectors.
 * @param A
 * @param B
 * @internal
 */
export function sub(A, B) {
    return [A[0] - B[0], A[1] - B[1]];
}
/**
 * Subtract vectors into an existing output vector (allocation-free).
 * @param out Output vector to mutate
 * @param A
 * @param B
 * @internal
 */
export function subInto(out, A, B) {
    out[0] = A[0] - B[0];
    out[1] = A[1] - B[1];
    return out;
}
/**
 * Vector multiplication by scalar
 * @param A
 * @param n
 * @internal
 */
export function mul(A, n) {
    return [A[0] * n, A[1] * n];
}
/**
 * Vector multiplication by scalar into an existing output vector (allocation-free).
 * @param out Output vector to mutate
 * @param A
 * @param n
 * @internal
 */
export function mulInto(out, A, n) {
    out[0] = A[0] * n;
    out[1] = A[1] * n;
    return out;
}
/**
 * Vector division by scalar.
 * @param A
 * @param n
 * @internal
 */
export function div(A, n) {
    return [A[0] / n, A[1] / n];
}
/**
 * Perpendicular rotation of a vector A
 * @param A
 * @internal
 */
export function per(A) {
    return [A[1], -A[0]];
}
/**
 * Perpendicular rotation into an existing output vector (allocation-free).
 * @param out Output vector to mutate
 * @param A
 * @internal
 */
export function perInto(out, A) {
    const temp = A[0];
    out[0] = A[1];
    out[1] = -temp;
    return out;
}
/**
 * Dot product
 * @param A
 * @param B
 * @internal
 */
export function dpr(A, B) {
    return A[0] * B[0] + A[1] * B[1];
}
/**
 * Get whether two vectors are equal.
 * @param A
 * @param B
 * @internal
 */
export function isEqual(A, B) {
    return A[0] === B[0] && A[1] === B[1];
}
/**
 * Length of the vector
 * @param A
 * @internal
 */
export function len(A) {
    return Math.hypot(A[0], A[1]);
}
/**
 * Length of the vector squared
 * @param A
 * @internal
 */
export function len2(A) {
    return A[0] * A[0] + A[1] * A[1];
}
/**
 * Dist length from A to B squared (inlined for performance).
 * @param A
 * @param B
 * @internal
 */
export function dist2(A, B) {
    const dx = A[0] - B[0];
    const dy = A[1] - B[1];
    return dx * dx + dy * dy;
}
/**
 * Get normalized / unit vector.
 * @param A
 * @internal
 */
export function uni(A) {
    return div(A, len(A));
}
/**
 * Dist length from A to B
 * @param A
 * @param B
 * @internal
 */
export function dist(A, B) {
    return Math.hypot(A[1] - B[1], A[0] - B[0]);
}
/**
 * Mean between two vectors or mid vector between two vectors
 * @param A
 * @param B
 * @internal
 */
export function med(A, B) {
    return mul(add(A, B), 0.5);
}
/**
 * Rotate a vector around another vector by r (radians)
 * @param A vector
 * @param C center
 * @param r rotation in radians
 * @internal
 */
export function rotAround(A, C, r) {
    const s = Math.sin(r);
    const c = Math.cos(r);
    const px = A[0] - C[0];
    const py = A[1] - C[1];
    const nx = px * c - py * s;
    const ny = px * s + py * c;
    return [nx + C[0], ny + C[1]];
}
/**
 * Rotate a vector around another vector by r (radians) into an existing output vector (allocation-free).
 * @param out Output vector to mutate
 * @param A vector
 * @param C center
 * @param r rotation in radians
 * @internal
 */
export function rotAroundInto(out, A, C, r) {
    const s = Math.sin(r);
    const c = Math.cos(r);
    const px = A[0] - C[0];
    const py = A[1] - C[1];
    const nx = px * c - py * s;
    const ny = px * s + py * c;
    out[0] = nx + C[0];
    out[1] = ny + C[1];
    return out;
}
/**
 * Interpolate vector A to B with a scalar t
 * @param A
 * @param B
 * @param t scalar
 * @internal
 */
export function lrp(A, B, t) {
    return add(A, mul(sub(B, A), t));
}
/**
 * Interpolate vector A to B with a scalar t into an existing output vector (allocation-free).
 * @param out Output vector to mutate
 * @param A
 * @param B
 * @param t scalar
 * @internal
 */
export function lrpInto(out, A, B, t) {
    const dx = B[0] - A[0];
    const dy = B[1] - A[1];
    out[0] = A[0] + dx * t;
    out[1] = A[1] + dy * t;
    return out;
}
/**
 * Project a point A in the direction B by a scalar c
 * @param A
 * @param B
 * @param c
 * @internal
 */
export function prj(A, B, c) {
    return add(A, mul(B, c));
}
/**
 * Project a point A in the direction B by a scalar c into an existing output vector (allocation-free).
 * @param out Output vector to mutate
 * @param A
 * @param B
 * @param c
 * @internal
 */
export function prjInto(out, A, B, c) {
    out[0] = A[0] + B[0] * c;
    out[1] = A[1] + B[1] * c;
    return out;
}
