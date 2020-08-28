/* Code generated by cmd/cgo; DO NOT EDIT. */

/* package command-line-arguments */


#line 1 "cgo-builtin-export-prolog"

#include <stddef.h> /* for ptrdiff_t below */

#ifndef GO_CGO_EXPORT_PROLOGUE_H
#define GO_CGO_EXPORT_PROLOGUE_H

#ifndef GO_CGO_GOSTRING_TYPEDEF
typedef struct { const char *p; ptrdiff_t n; } _GoString_;
#endif

#endif

/* Start of preamble from import "C" comments.  */




/* End of preamble from import "C" comments.  */


/* Start of boilerplate cgo prologue.  */
#line 1 "cgo-gcc-export-header-prolog"

#ifndef GO_CGO_PROLOGUE_H
#define GO_CGO_PROLOGUE_H

typedef signed char GoInt8;
typedef unsigned char GoUint8;
typedef short GoInt16;
typedef unsigned short GoUint16;
typedef int GoInt32;
typedef unsigned int GoUint32;
typedef long long GoInt64;
typedef unsigned long long GoUint64;
typedef GoInt64 GoInt;
typedef GoUint64 GoUint;
typedef __SIZE_TYPE__ GoUintptr;
typedef float GoFloat32;
typedef double GoFloat64;
typedef float _Complex GoComplex64;
typedef double _Complex GoComplex128;

/*
  static assertion to make sure the file is being used on architecture
  at least with matching size of GoInt.
*/
typedef char _check_for_64_bit_pointer_matching_GoInt[sizeof(void*)==64/8 ? 1:-1];

#ifndef GO_CGO_GOSTRING_TYPEDEF
typedef _GoString_ GoString;
#endif
typedef void *GoMap;
typedef void *GoChan;
typedef struct { void *t; void *v; } GoInterface;
typedef struct { void *data; GoInt len; GoInt cap; } GoSlice;

#endif

/* End of boilerplate cgo prologue.  */

#ifdef __cplusplus
extern "C" {
#endif


// NodeDensity calculates node density

extern GoFloat64 NodeDensity(GoFloat64 p0, GoFloat64 p1, GoFloat64 p2, GoInt p3);

// NodeFarness calculates farness

extern GoFloat64 NodeFarness(GoFloat64 p0, GoFloat64 p1, GoFloat64 p2, GoInt p3);

// NodeCycles calculates network cycles

extern GoInt NodeCycles(GoFloat64 p0, GoFloat64 p1, GoFloat64 p2, GoInt p3);

// NodeHarmonic calculates harmonic closeness

extern GoFloat64 NodeHarmonic(GoFloat64 p0, GoFloat64 p1, GoFloat64 p2, GoInt p3);

// NodeBeta calculates the "gravity" index

extern GoFloat64 NodeBeta(GoFloat64 p0, GoFloat64 p1, GoFloat64 p2, GoInt p3);

// NodeHarmonicAngular calculates angular harmonic closeness

extern GoFloat64 NodeHarmonicAngular(GoFloat64 p0, GoFloat64 p1, GoFloat64 p2, GoInt p3);

// NodeBetweenness calculates node betweenness

extern GoFloat64 NodeBetweenness(GoFloat64 p0, GoFloat64 p1);

// NodeBetweennessBeta calculates node betweenness weighted by beta

extern GoFloat64 NodeBetweennessBeta(GoFloat64 p0, GoFloat64 p1);

extern void MakeGraph();

extern void PrintGraph();

#ifdef __cplusplus
}
#endif