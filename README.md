# 贞洁待遇与天使誓约保护

Angel-Temple-Vow-Protection **2.2.0** — 针对本地 DoL 0.5.12.13 整合环境的补丁项目。

失去生殖器贞洁后保留天使、神殿誓约和指定事件的贞洁待遇；**不伪造真实经历**。

## 功能

- 阻止 `fallenTransform` 宏导致的天使丧失／堕落，不自动恢复已损失的形态和进度。
- 阻止两条生殖器行为破誓路径，不新增相应破誓次数。
- 对 prospective / initiate / monk / priest 身份恢复并维护神殿誓约标记；不清零历史破誓次数。
- 豁免首次生殖器失贞的一次性 -50 纯洁惩罚；其他惩罚不变。
- 保留每日纯洁计算的 +2 加项及 1000 上限，保留其他模组对最终数值的影响。
- 延续 2.1.0 的指定检查／事件资格：神殿、悉尼检查、神殿贞操带服务、布莱尔相关表演资格、地下场所入场、艾弗里特定对话、成人用品店特殊事件、哈珀摄像事件分支和调试检查。

**“待遇”不都是正面奖励。**成人用品店对应的是负面特殊遭遇；当前版本为保持旧版范围而保留。神殿以外的其他条件、NPC 自己的誓约、事件冷却与实际行为结算不被全局绕过。详见 [事件清单](docs/EVENTS.zh-CN.md)。

## 安装与验证

1. 备份存档，禁用同名旧版 1.0.0 / 2.0.0 / 2.1.0，只加载一个版本。
2. 使用本地构建得到的 `dist/Angel-Temple-Vow-Protection-2.2.0.mod.zip`，通过 Lyra ModLoader 导入，不要解压。
3. 在枫叶框架、枯木逢春、归途之书等目标 MOD 之后加载，重新启动游戏。
4. 查看加载日志：本项目应有 **25 条 TweeReplacer 规则、2 条 ReplacePatcher 规则**成功，无本项目匹配失败。
5. 使用备份存档，按 [游戏内验证清单](docs/TESTING.zh-CN.md) 测试。

目标依赖：GameVersion =0.5.12.13，maplebirch =5.6.2，deadwood-reblooms =2.5.8，revelation-the-book-of-return =1.4.6，TweeReplacer >=1.7.0，ReplacePatcher >=1.3.0，ModLoader >=2.60.1。其他整合包、版本或加载顺序不保证兼容。

## 开发

需要 Python 3.10+、Node.js 20+，无需安装第三方依赖。

```powershell
python tools/build.py --export "G:\path\Degrees-of Lewdity_ExportData.zip"
python -m unittest discover -s tests -v
node --test tests/runtime.test.cjs
```

对真实导出包运行完整集成测试：

```powershell
$env:DOL_EXPORT = "G:\path\Degrees-of Lewdity_ExportData.zip"
python -m unittest discover -s tests -v
```

构建器接受未启用本项目的目标环境导出包，也能依据导出的旧版清单和失败日志，在内存中撤销已成功应用的 1.0.0 / 2.0.0 / 2.1.0 补丁后验证新补丁。不修改输入文件，不撤销其他 MOD。无法安全还原或匹配数量变化时直接报错，不悄悄发布残缺包。

## 文件与隐私

- `src/`：运行时与最小补丁规则。
- `tools/build.py`：构建、旧版参考还原及严格匹配检查。
- `tests/`：运行时、条件语义、构建及可选本地整合测试。
- `docs/`：变更、事件与验证说明。
- `dist/`：本地生成安装包（不进入 Git）。

仓库不收录完整游戏代码、游戏资源、用户存档、导出包、第三方 MOD 原包或账号凭据。构建产物仅包含必要补丁片段，不包含完整游戏页面。

## 卸载与边界

禁用并重启游戏后，本版运行时资格判定不再存在，不通过存档标记继续授予待遇。升级时会删除本项目旧版的 `$angelTempleVowProtection` 标记。

**已写入存档的神殿誓约恢复、已产生的事件奖励等不会自动回滚。**若需恢复原状态，请使用安装前备份。不会自动修复历史堕落、天使进度、创伤或破誓次数。不要将诊断开关 `window.AngelTempleVowProtection.setEnabled(false)` 当作完整卸载。

验证等级：静态补丁检查与自动化测试；**尚未完成实际游戏全流程验证**。本项目是独立兼容性补丁，不是游戏或依赖 MOD 的官方发行版。
