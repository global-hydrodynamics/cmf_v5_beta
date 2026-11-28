module inpmat_mod
    use, intrinsic :: ieee_arithmetic, only: ieee_is_finite
    use PARKIND1, only: &
    &   JPRM, JPRB, JPIM, JPIB
    use YOS_CMF_INPUT, only: LOGNAM, MODEL_NX => NX, MODEL_NY => NY, MODEL_NLFP => NLFP
    use funit_mod, only: INQUIRE_FID
    use YOS_CMF_MAP, only: &
    &   NSEQMAX, I1SEQX, I1SEQY

    use, intrinsic :: ieee_arithmetic, only: ieee_is_finite
    implicit none
    private
    public :: Inpmat, load_inpmat_files, move_append_inpmat

    type Inpmat
        integer :: nxin, nyin
        integer :: &
        &   inpn
        integer, allocatable :: &
        &   inpx(:,:,:), inpy(:,:,:)
        real(kind=JPRB), allocatable :: &
        &   inpa(:,:,:)

        contains

        procedure :: map2vec_intrp => map2vec_intrp
        procedure :: matches_shape

    end type Inpmat

contains

subroutine map2vec_intrp(self, map, vec)
    class(Inpmat)   , intent(in)  :: self
    real(kind=JPRM), intent(in)  :: map(:,:)
    real(kind=JPRB), intent(out) :: vec(:)
    real(kind=JPRM), parameter :: fill_val = 1.e16_JPRM
    integer :: iseq, ix, iy, inpi, ixin, iyin
    real(kind=JPRB) :: grda

    !$omp parallel do private(ix, iy, inpi, ixin, iyin, grda)
    do iseq = 1, NSEQMAX
        vec(iseq) = 0.0_JPRB
        ix = I1SEQX(iseq)
        iy = I1SEQY(iseq)
        grda = 0.0_JPRB
        do inpi = 1, self%INPN
            if ( self%inpa(ix,iy,inpi) <= 0.0_JPRB ) exit
            ixin = self%INPX(ix, iy, inpi)
            iyin = self%INPY(ix, iy, inpi)
            if (ixin < 1) exit
            if (isnan(map(ixin,iyin))) cycle
            if ( map(ixin,iyin) < 0.0_JPRM ) cycle
            if ( map(ixin,iyin) >= fill_val ) cycle
            vec(iseq) = vec(iseq) + real(map(ixin,iyin), kind=JPRB) * self%inpa(ix,iy,inpi)
            grda      = grda      +                  self%inpa(ix,iy,inpi)
        enddo
        if (grda > 0.0_JPRB) vec(iseq) = vec(iseq) / grda
    enddo
    !$omp end parallel do
end subroutine map2vec_intrp

subroutine load_inpmat_files(obj, diminfo_file, inpmat_file)
    type(Inpmat), intent(out) :: obj
    character(len=*), intent(in) :: diminfo_file, inpmat_file
    integer(kind=JPIM) :: nx_dst, ny_dst, nlfp_dst, nxin, nyin
    real(kind=JPRB) :: bounds(8)

    call read_inpmat_diminfo(diminfo_file, nx_dst, ny_dst, nlfp_dst, nxin, nyin, obj%inpn, bounds)
    if (nx_dst /= MODEL_NX .or. ny_dst /= MODEL_NY .or. nlfp_dst /= MODEL_NLFP) then
        write(LOGNAM, '(a)') '[load_inpmat_files ERROR] destination shape mismatch'
        stop 1
    endif
    if (.not. all(ieee_is_finite(bounds))) then
        write(LOGNAM, '(a)') '[load_inpmat_files ERROR] non-finite domain bounds'
        stop 1
    endif
    obj%nxin = nxin
    obj%nyin = nyin
    call read_inpmat_file(inpmat_file, obj%inpx, obj%inpy, obj%inpa, obj%inpn)
    call validate_inpmat(obj)
end subroutine load_inpmat_files

subroutine read_inpmat_diminfo(path, nx_dst, ny_dst, nlfp_dst, nxin_out, nyin_out, inpn_out, bounds)
    character(len=*), intent(in) :: path
    integer(kind=JPIM), intent(out) :: nx_dst, ny_dst, nlfp_dst, nxin_out, nyin_out, inpn_out
    real(kind=JPRB), intent(out) :: bounds(8)
    integer(kind=JPIM) :: NX, NY, NLFP, NXIN, NYIN, INPN
    real(kind=JPRB) :: WEST, EAST, NORTH, SOUTH, WESTIN, EASTIN, NORTHIN, SOUTHIN
    character(len=512) :: INPMAT_FILE
    character(len=8) :: OLATIN
    integer :: unit, ios

    namelist /DIMINFO/ NX, NY, NLFP, WEST, EAST, NORTH, SOUTH
    namelist /INPUTDIM/ INPMAT_FILE, NXIN, NYIN, INPN, WESTIN, EASTIN, NORTHIN, SOUTHIN, OLATIN

    unit = INQUIRE_FID()
    open(unit, file=trim(path), form='formatted', status='old', action='read', iostat=ios)
    if (ios /= 0) then
        write(LOGNAM, '(2a)') '[inpmat_mod/read_inpmat_diminfo ERROR] cannot open: ', trim(path)
        stop 1
    endif
    NX = -1
    NY = -1
    NLFP = -1
    WEST = 1.0E30_JPRB
    EAST = -1.0E30_JPRB
    NORTH = -1.0E30_JPRB
    SOUTH = 1.0E30_JPRB
    NXIN = -1
    NYIN = -1
    INPN = -1
    INPMAT_FILE = ''
    WESTIN = 1.0E30_JPRB
    EASTIN = -1.0E30_JPRB
    NORTHIN = -1.0E30_JPRB
    SOUTHIN = 1.0E30_JPRB
    OLATIN = ''
    read(unit, nml=DIMINFO, iostat=ios)
    if (ios /= 0) then
        write(LOGNAM, '(2a)') '[inpmat_mod/read_inpmat_diminfo ERROR] invalid DIMINFO Namelist: ', trim(path)
        close(unit)
        stop 1
    endif
    rewind(unit)
    read(unit, nml=INPUTDIM, iostat=ios)
    close(unit)
    if (ios /= 0) then
        write(LOGNAM, '(2a)') '[inpmat_mod/read_inpmat_diminfo ERROR] invalid INPUTDIM Namelist: ', trim(path)
        stop 1
    endif
    if (min(NX, NY, NLFP, NXIN, NYIN, INPN) < 1 .or. len_trim(INPMAT_FILE) == 0) then
        write(LOGNAM, '(2a)') '[inpmat_mod/read_inpmat_diminfo ERROR] missing or non-positive field: ', trim(path)
        stop 1
    endif
    if (.not. all(ieee_is_finite([WEST, EAST, NORTH, SOUTH])) .or. &
        EAST <= WEST .or. NORTH <= SOUTH) then
        write(LOGNAM, '(2a)') '[inpmat_mod/read_inpmat_diminfo ERROR] non-finite or invalid model-grid bounds: ', trim(path)
        stop 1
    endif
    if (.not. all(ieee_is_finite([WESTIN, EASTIN, NORTHIN, SOUTHIN])) .or. &
        EASTIN <= WESTIN .or. NORTHIN <= SOUTHIN .or. &
        (trim(OLATIN) /= 'NtoS' .and. trim(OLATIN) /= 'StoN')) then
        write(LOGNAM, '(2a)') '[inpmat_mod/read_inpmat_diminfo ERROR] invalid INPUTDIM grid metadata: ', trim(path)
        stop 1
    endif
    nx_dst = NX
    ny_dst = NY
    nlfp_dst = NLFP
    nxin_out = NXIN
    nyin_out = NYIN
    inpn_out = INPN
    bounds = [WEST, EAST, NORTH, SOUTH, WESTIN, EASTIN, NORTHIN, SOUTHIN]
end subroutine read_inpmat_diminfo


subroutine read_inpmat_file(path, inpx, inpy, inpa, inpn)
    character(len=*), intent(in) :: path
    integer(kind=JPIM), allocatable, intent(out) :: inpx(:,:,:), inpy(:,:,:)
    real(kind=JPRB), allocatable, intent(out) :: inpa(:,:,:)
    integer(kind=JPIM), intent(in) :: inpn
    real(kind=JPRM), allocatable :: rinp(:,:,:)
    integer, parameter :: byte_recl = 4
    integer :: unit, ios
    integer(kind=JPIB) :: file_size, expected_size
    logical :: exists

    inquire(file=trim(path), exist=exists, size=file_size, iostat=ios)
    if (ios /= 0 .or. .not. exists) then
        write(LOGNAM, '(2a)') '[inpmat_mod/read_inpmat_file ERROR] cannot stat: ', trim(path)
        stop 1
    endif
    expected_size = 3_JPIB * int(MODEL_NX, JPIB) * int(MODEL_NY, JPIB) * int(inpn, JPIB) * byte_recl
    if (file_size /= expected_size) then
        write(LOGNAM, '(2a)') '[inpmat_mod/read_inpmat_file ERROR] incorrect file size: ', trim(path)
        write(LOGNAM, '(a,i0)') '    actual:   ', file_size
        write(LOGNAM, '(a,i0)') '    expected: ', expected_size
        stop 1
    endif

    allocate(inpx(MODEL_NX,MODEL_NY,inpn), inpy(MODEL_NX,MODEL_NY,inpn), &
        inpa(MODEL_NX,MODEL_NY,inpn), rinp(MODEL_NX,MODEL_NY,inpn))
    unit = INQUIRE_FID()
    open(unit, file=trim(path), form='unformatted', access='stream', status='old', action='read', iostat=ios)
    if (ios /= 0) then
        write(LOGNAM, '(2a)') '[inpmat_mod/read_inpmat_file ERROR] cannot open: ', trim(path)
        stop 1
    endif
    read(unit, iostat=ios) inpx(:,:,:)
    if (ios == 0) read(unit, iostat=ios) inpy(:,:,:)
    if (ios == 0) read(unit, iostat=ios) rinp(:,:,:)
    close(unit)
    if (ios /= 0) then
        write(LOGNAM, '(2a)') '[inpmat_mod/read_inpmat_file ERROR] cannot read: ', trim(path)
        stop 1
    endif
    inpa(:,:,:) = real(rinp(:,:,:), kind=JPRB)
    deallocate(rinp)
end subroutine read_inpmat_file


subroutine validate_inpmat(self)
    class(Inpmat), intent(in) :: self
    integer(kind=JPIM) :: inpi

    if (any(self%inpx < 0) .or. any(self%inpx > self%nxin)) then
        write(LOGNAM, '(a)') '[inpmat_mod/validate_inpmat ERROR] inpx is out of range'
        stop 1
    endif
    if (any(self%inpy < 0) .or. any(self%inpy > self%nyin)) then
        write(LOGNAM, '(a)') '[inpmat_mod/validate_inpmat ERROR] inpy is out of range'
        stop 1
    endif
    if (any(.not. ieee_is_finite(self%inpa)) .or. any(self%inpa < 0.0_JPRB)) then
        write(LOGNAM, '(a)') '[inpmat_mod/validate_inpmat ERROR] inpa must be finite and non-negative'
        stop 1
    endif
    if (any((self%inpx > 0) .neqv. (self%inpy > 0)) .or. &
    &   any((self%inpx > 0) .neqv. (self%inpa > 0.0_JPRB))) then
        write(LOGNAM, '(a)') '[inpmat_mod/validate_inpmat ERROR] inconsistent zero padding'
        stop 1
    endif
    do inpi = 2, self%inpn
        if (any((self%inpa(:,:,inpi) > 0.0_JPRB) .and. (self%inpa(:,:,inpi-1) <= 0.0_JPRB))) then
            write(LOGNAM, '(a)') '[inpmat_mod/validate_inpmat ERROR] non-contiguous input slots'
            stop 1
        endif
    enddo
end subroutine validate_inpmat


logical function matches_shape(self, nxin, nyin) result(matches)
    class(Inpmat), intent(in) :: self
    integer(kind=JPIM), intent(in) :: nxin, nyin
    matches = self%nxin == nxin .and. self%nyin == nyin
end function matches_shape

subroutine move_append_inpmat(inpmats, ainpmat)
    type(Inpmat), allocatable, intent(inout) :: inpmats(:)
    type(Inpmat),              intent(inout) :: ainpmat
    type(Inpmat), allocatable                :: tmp(:)
    integer :: i, old_size

    if (.not. allocated(inpmats)) then
        allocate(inpmats(1))
        call move_inpmat(ainpmat, inpmats(1))
        return
    endif
    old_size = size(inpmats)
    allocate(tmp(old_size + 1))
    do i = 1, old_size
        call move_inpmat(inpmats(i), tmp(i))
    enddo
    call move_inpmat(ainpmat, tmp(old_size + 1))
    call move_alloc(tmp, inpmats)
end subroutine move_append_inpmat


subroutine move_inpmat(source, destination)
    type(Inpmat), intent(inout) :: source
    type(Inpmat), intent(out) :: destination

    destination%nxin = source%nxin
    destination%nyin = source%nyin
    destination%inpn = source%inpn
    call move_alloc(source%inpx, destination%inpx)
    call move_alloc(source%inpy, destination%inpy)
    call move_alloc(source%inpa, destination%inpa)
    source%inpn = 0_JPIM
end subroutine move_inpmat

end module inpmat_mod
