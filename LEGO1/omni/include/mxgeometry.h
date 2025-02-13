#ifndef MXGEOMETRY_H
#define MXGEOMETRY_H

#include "mxutilities.h"

template <class T>
class MxPoint {
protected:
	T m_x;
	T m_y;

public:
	MxPoint() {}
	MxPoint(const MxPoint& p_p)
	{
		m_x = p_p.m_x;
		m_y = p_p.m_y;
	}
	MxPoint(T p_x, T p_y)
	{
		m_x = p_x;
		m_y = p_y;
	}
	T GetX() const { return m_x; }
	T GetY() const { return m_y; }
	void SetX(T p_x) { m_x = p_x; }
	void SetY(T p_y) { m_y = p_y; }
	void operator+=(const MxPoint& p_p)
	{
		m_x += p_p.m_x;
		m_y += p_p.m_y;
	}
	void operator-=(const MxPoint& p_p)
	{
		m_x -= p_p.m_x;
		m_y -= p_p.m_y;
	}
	MxPoint operator+(const MxPoint& p_p) const { return MxPoint(m_x + p_p.m_x, m_y + p_p.m_y); }
	MxPoint operator-(const MxPoint& p_p) const { return MxPoint(m_x - p_p.m_x, m_y - p_p.m_y); }
};

template <class T>
class MxSize {
protected:
	T m_width;
	T m_height;

public:
	MxSize() {}
	MxSize(const MxSize& p_s)
	{
		m_width = p_s.m_width;
		m_height = p_s.m_height;
	}
	MxSize(T p_width, T p_height)
	{
		m_width = p_width;
		m_height = p_height;
	}
	T GetWidth() const { return m_width; }
	T GetHeight() const { return m_height; }
	void SetWidth(T p_width) { m_width = p_width; }
	void SetHeight(T p_height) { m_height = p_height; }
};

template <class T>
class MxRect {
protected:
	T m_left;
	T m_top;
	T m_right;
	T m_bottom;

public:
	MxRect() {}
	MxRect(const MxRect& p_r)
	{
		m_left = p_r.m_left;
		m_top = p_r.m_top;
		m_right = p_r.m_right;
		m_bottom = p_r.m_bottom;
	}
	MxRect(T p_l, T p_t, T p_r, T p_b)
	{
		m_left = p_l;
		m_top = p_t;
		m_right = p_r;
		m_bottom = p_b;
	}
	MxRect(const MxPoint<T>& p_p, const MxSize<T>& p_s)
	{
		m_left = p_p.GetX();
		m_top = p_p.GetY();
		m_right = p_p.GetX() + p_s.GetWidth() - 1;
		m_bottom = p_p.GetY() + p_s.GetHeight() - 1;
	}
	T GetLeft() const { return m_left; }
	void SetLeft(T p_left) { m_left = p_left; }
	T GetTop() const { return m_top; }
	void SetTop(T p_top) { m_top = p_top; }
	T GetRight() const { return m_right; }
	void SetRight(T p_right) { m_right = p_right; }
	T GetBottom() const { return m_bottom; }
	void SetBottom(T p_bottom) { m_bottom = p_bottom; }
	T GetWidth() const { return (m_right - m_left + 1); }
	T GetHeight() const { return (m_bottom - m_top + 1); }
	MxPoint<T> GetLT() const { return MxPoint<T>(m_left, m_top); }
	MxPoint<T> GetRB() const { return MxPoint<T>(m_right, m_bottom); }
	MxBool Empty() const { return m_left >= m_right || m_top >= m_bottom; }
	MxBool Contains(const MxPoint<T>& p_p) const
	{
		return p_p.GetX() >= m_left && p_p.GetX() <= m_right && p_p.GetY() >= m_top && p_p.GetY() <= m_bottom;
	}
	MxBool Intersects(const MxRect& p_r) const
	{
		return p_r.m_right > m_left && p_r.m_left < m_right && p_r.m_bottom > m_top && p_r.m_top < m_bottom;
	}
	void operator=(const MxRect& p_r)
	{
		m_left = p_r.m_left;
		m_top = p_r.m_top;
		m_right = p_r.m_right;
		m_bottom = p_r.m_bottom;
	}
	MxBool operator==(const MxRect& p_r) const
	{
		return m_left == p_r.m_left && m_top == p_r.m_top && m_right == p_r.m_right && m_bottom == p_r.m_bottom;
	}
	MxBool operator!=(const MxRect& p_r) const { return !operator==(p_r); }
	void operator+=(const MxPoint<T>& p_p)
	{
		m_left += p_p.GetX();
		m_top += p_p.GetY();
		m_right += p_p.GetX();
		m_bottom += p_p.GetY();
	}
	void operator-=(const MxPoint<T>& p_p)
	{
		m_left -= p_p.GetX();
		m_top -= p_p.GetY();
		m_right -= p_p.GetX();
		m_bottom -= p_p.GetY();
	}
	void operator&=(const MxRect& p_r)
	{
		m_left = Max(p_r.m_left, m_left);
		m_top = Max(p_r.m_top, m_top);
		m_right = Min(p_r.m_right, m_right);
		m_bottom = Min(p_r.m_bottom, m_bottom);
	}
	void operator|=(const MxRect& p_r)
	{
		m_left = Min(p_r.m_left, m_left);
		m_top = Min(p_r.m_top, m_top);
		m_right = Max(p_r.m_right, m_right);
		m_bottom = Max(p_r.m_bottom, m_bottom);
	}
	MxRect operator+(const MxPoint<T>& p_p) const
	{
		return MxRect(m_left + p_p.GetX(), m_top + p_p.GetY(), m_left + p_p.GetX(), m_bottom + p_p.GetY());
	}
	MxRect operator-(const MxPoint<T>& p_p) const
	{
		return MxRect(m_left - p_p.GetX(), m_top - p_p.GetY(), m_left - p_p.GetX(), m_bottom - p_p.GetY());
	}
	MxRect operator&(const MxRect& p_r) const
	{
		return MxRect(
			Max(p_r.m_left, m_left),
			Max(p_r.m_top, m_top),
			Min(p_r.m_right, m_right),
			Min(p_r.m_bottom, m_bottom)
		);
	}
	MxRect operator|(const MxRect& p_r) const
	{
		return MxRect(
			Min(p_r.m_left, m_left),
			Min(p_r.m_top, m_top),
			Max(p_r.m_right, m_right),
			Max(p_r.m_bottom, m_bottom)
		);
	}
};

#endif // MXGEOMETRY_H
