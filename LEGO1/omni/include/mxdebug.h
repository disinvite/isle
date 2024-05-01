#ifndef MXDEBUG_H
#define MXDEBUG_H

#ifdef _DEBUG

void MxTrace(const char* format, ...);

#else

inline void MxTrace(const char*, ...)
{
}

#endif // _DEBUG

#endif // MXDEBUG_H
