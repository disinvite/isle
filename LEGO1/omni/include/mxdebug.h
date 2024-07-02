#ifndef MXDEBUG_H
#define MXDEBUG_H

#ifdef _DEBUG

#define MxTrace _MxTrace

void _MxTrace(const char* format, ...);
int DebugHeapState();

#else

#define MxTrace(args)

#endif // _DEBUG

#endif // MXDEBUG_H
