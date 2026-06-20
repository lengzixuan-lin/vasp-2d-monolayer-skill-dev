subroutine msd(xout, xin, nrepeat, ntotal)
    ! autocorrelation function <|A(t0)-A(t+t0)|^2>

    real, intent(out) :: xout(nrepeat)
    real, intent(in) :: xin(ntotal)
    integer, intent(in) :: nrepeat, ntotal

    real :: tdata(nrepeat) ! temporary data in a period of sampling.
    integer :: t0, t
    integer :: i, j

    tdata=0.d0
    xout=0.d0
    do i=1,ntotal
        if (i .le. nrepeat) then
            tdata(i)=xin(i)
        else
            t0=mod(i,nrepeat)
            if (t0 == 0) t0=nrepeat
            tdata(t0)=xin(i)
            do j=2,nrepeat
                ! t
                t=t0-j+1
                if (t .le. 0) t=t+nrepeat
                xout(j)=xout(j)+(tdata(t0)-tdata(t))**2
            enddo
        endif
    enddo
    xout=xout/(ntotal-nrepeat)
    return
end subroutine msd
