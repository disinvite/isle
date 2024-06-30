#if !defined(AFX_DETECTDX5_H)
#define AFX_DETECTDX5_H

#include <windows.h>

extern BOOL DetectDirectX5();

extern void DetectDirectX(unsigned int* p_version, BOOL* p_found);

// GLOBAL: CONFIG 0x4064e8
// IID_IDirectDraw2

// GLOBAL: CONFIG 0x406518
// IID_IDirectDrawSurface3

#endif // !defined(AFX_DETECTDX5_H)
