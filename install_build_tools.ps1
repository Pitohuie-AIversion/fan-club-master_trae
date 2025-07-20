# Fan Club MkIV - 编译工具自动安装脚本
# 此脚本将自动安装 ARM GCC 工具链和 Make 工具

# 检查管理员权限
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# 显示标题
Write-Host "=================================" -ForegroundColor Cyan
Write-Host "Fan Club MkIV 编译工具安装脚本" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# 检查管理员权限
if (-not (Test-Administrator)) {
    Write-Host "警告: 建议以管理员身份运行此脚本以获得最佳安装体验" -ForegroundColor Yellow
    Write-Host "继续安装可能需要手动确认某些操作" -ForegroundColor Yellow
    Write-Host ""
}

# 检查当前工具状态
Write-Host "检查当前系统状态..." -ForegroundColor Green

# 检查 ARM GCC
try {
    $armGccVersion = & arm-none-eabi-gcc --version 2>$null
    Write-Host "✅ ARM GCC 工具链已安装" -ForegroundColor Green
    $armGccInstalled = $true
} catch {
    Write-Host "❌ ARM GCC 工具链未安装" -ForegroundColor Red
    $armGccInstalled = $false
}

# 检查 Make
try {
    $makeVersion = & make --version 2>$null
    Write-Host "✅ Make 工具已安装" -ForegroundColor Green
    $makeInstalled = $true
} catch {
    Write-Host "❌ Make 工具未安装" -ForegroundColor Red
    $makeInstalled = $false
}

Write-Host ""

# 如果都已安装，退出
if ($armGccInstalled -and $makeInstalled) {
    Write-Host "所有必要工具已安装，无需继续安装" -ForegroundColor Green
    Write-Host "您可以直接开始编译项目" -ForegroundColor Green
    exit 0
}

# 安装选项菜单
Write-Host "请选择安装方式:" -ForegroundColor Yellow
Write-Host "1. 使用 Chocolatey 自动安装 (推荐)" -ForegroundColor White
Write-Host "2. 手动下载安装包" -ForegroundColor White
Write-Host "3. 使用 MSYS2 安装" -ForegroundColor White
Write-Host "4. 退出" -ForegroundColor White
Write-Host ""

$choice = Read-Host "请输入选择 (1-4)"

switch ($choice) {
    "1" {
        Write-Host "\n使用 Chocolatey 安装..." -ForegroundColor Green
        
        # 检查 Chocolatey 是否已安装
        try {
            $chocoVersion = & choco --version 2>$null
            Write-Host "Chocolatey 已安装: $chocoVersion" -ForegroundColor Green
        } catch {
            Write-Host "安装 Chocolatey..." -ForegroundColor Yellow
            try {
                Set-ExecutionPolicy Bypass -Scope Process -Force
                [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
                iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
                Write-Host "Chocolatey 安装成功" -ForegroundColor Green
            } catch {
                Write-Host "Chocolatey 安装失败: $($_.Exception.Message)" -ForegroundColor Red
                Write-Host "请尝试手动安装或选择其他安装方式" -ForegroundColor Yellow
                exit 1
            }
        }
        
        # 安装 ARM GCC 工具链
        if (-not $armGccInstalled) {
            Write-Host "安装 ARM GCC 工具链..." -ForegroundColor Yellow
            try {
                & choco install gcc-arm-embedded -y
                Write-Host "ARM GCC 工具链安装成功" -ForegroundColor Green
            } catch {
                Write-Host "ARM GCC 工具链安装失败: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
        
        # 安装 Make
        if (-not $makeInstalled) {
            Write-Host "安装 Make 工具..." -ForegroundColor Yellow
            try {
                & choco install make -y
                Write-Host "Make 工具安装成功" -ForegroundColor Green
            } catch {
                Write-Host "Make 工具安装失败: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }
    
    "2" {
        Write-Host "\n手动安装指南:" -ForegroundColor Green
        Write-Host ""
        Write-Host "ARM GCC 工具链:" -ForegroundColor Yellow
        Write-Host "1. 访问: https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads"
        Write-Host "2. 下载 Windows 版本的 arm-gnu-toolchain-*-mingw-w64-i686-arm-none-eabi.exe"
        Write-Host "3. 运行安装程序，确保勾选 'Add path to environment variable'"
        Write-Host ""
        Write-Host "Make 工具:" -ForegroundColor Yellow
        Write-Host "1. 访问: http://gnuwin32.sourceforge.net/packages/make.htm"
        Write-Host "2. 下载并安装 Complete package, except sources"
        Write-Host "3. 将安装目录的 bin 文件夹添加到系统 PATH"
        Write-Host ""
        Write-Host "安装完成后，重启 PowerShell 并运行验证命令" -ForegroundColor Green
    }
    
    "3" {
        Write-Host "\nMSYS2 安装指南:" -ForegroundColor Green
        Write-Host ""
        Write-Host "1. 下载并安装 MSYS2: https://www.msys2.org/"
        Write-Host "2. 打开 MSYS2 终端，运行以下命令:"
        Write-Host "   pacman -S mingw-w64-x86_64-arm-none-eabi-gcc"
        Write-Host "   pacman -S mingw-w64-x86_64-arm-none-eabi-newlib"
        Write-Host "   pacman -S make"
        Write-Host "3. 将 MSYS2 的 mingw64/bin 目录添加到系统 PATH"
        Write-Host "   通常位于: C:\\msys64\\mingw64\\bin"
        Write-Host ""
    }
    
    "4" {
        Write-Host "退出安装" -ForegroundColor Yellow
        exit 0
    }
    
    default {
        Write-Host "无效选择，退出安装" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "=================================" -ForegroundColor Cyan
Write-Host "安装完成!" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步操作:" -ForegroundColor Green
Write-Host "1. 重启 PowerShell 或命令提示符" -ForegroundColor White
Write-Host "2. 运行以下命令验证安装:" -ForegroundColor White
Write-Host "   arm-none-eabi-gcc --version" -ForegroundColor Gray
Write-Host "   make --version" -ForegroundColor Gray
Write-Host "3. 进入 slave 目录并运行 make 编译" -ForegroundColor White
Write-Host ""
Write-Host "如果遇到问题，请参考 MAKE_COMPILATION_GUIDE.md 文档" -ForegroundColor Yellow

# 询问是否立即验证
Write-Host ""
$verify = Read-Host "是否现在验证安装? (y/n)"
if ($verify -eq "y" -or $verify -eq "Y") {
    Write-Host "\n验证安装..." -ForegroundColor Green
    
    # 重新加载环境变量
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    try {
        Write-Host "ARM GCC 版本:" -ForegroundColor Yellow
        & arm-none-eabi-gcc --version
        Write-Host "✅ ARM GCC 工具链验证成功" -ForegroundColor Green
    } catch {
        Write-Host "❌ ARM GCC 工具链验证失败" -ForegroundColor Red
        Write-Host "请重启 PowerShell 后再次尝试" -ForegroundColor Yellow
    }
    
    Write-Host ""
    
    try {
        Write-Host "Make 版本:" -ForegroundColor Yellow
        & make --version
        Write-Host "✅ Make 工具验证成功" -ForegroundColor Green
    } catch {
        Write-Host "❌ Make 工具验证失败" -ForegroundColor Red
        Write-Host "请重启 PowerShell 后再次尝试" -ForegroundColor Yellow
    }
}

Write-Host "\n脚本执行完成!" -ForegroundColor Green